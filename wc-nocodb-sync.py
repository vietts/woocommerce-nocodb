#!/usr/bin/env python3
"""
WooCommerce → NocoDB Sync Script
Sincronizza ordini e clienti da WooCommerce a NocoDB con deduplicazione intelligente.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import time

# ============================================================================
# CONFIGURAZIONE LOGGING
# ============================================================================

LOG_FILE = "/tmp/wc-nocodb-sync.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# WOOCOMMERCE CLIENT
# ============================================================================

class WooCommerceClient:
    """Client per interagire con WooCommerce REST API v3"""

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = store_url.rstrip('/') + '/wp-json/wc/v3'
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.rate_limit_wait = 5  # secondi di attesa se rate limited

    def get_orders(self, statuses: List[str] = None, days_back: int = 7) -> List[Dict]:
        """
        Recupera ordini da WooCommerce.

        Args:
            statuses: Lista di stati ('processing', 'pending', 'on-hold', etc.)
            days_back: Recupera ordini modificati negli ultimi N giorni

        Returns:
            Lista di ordini con tutti i dettagli
        """
        if statuses is None:
            statuses = ['processing', 'pending', 'on-hold']

        all_orders = []
        page = 1
        per_page = 100

        # Calcola data limite
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        while True:
            params = {
                'status': ','.join(statuses),
                'per_page': per_page,
                'page': page,
                'orderby': 'date',
                'order': 'desc'
            }

            try:
                logger.info(f"📦 Recuperando ordini da WooCommerce (pagina {page})...")
                response = self.session.get(
                    f"{self.base_url}/orders",
                    params=params,
                    timeout=10
                )

                if response.status_code == 429:  # Rate limit
                    logger.warning(f"⏱️ Rate limit raggiunto, attendo {self.rate_limit_wait}s...")
                    time.sleep(self.rate_limit_wait)
                    continue

                response.raise_for_status()
                orders = response.json()

                if not orders:
                    break

                # Filtra ordini per data di modifica e stato
                # Se full_sync: prendi tutti
                # Altrimenti: solo ultimi 7 giorni + stato processing/pending
                if days_back >= 1000:  # full_sync
                    filtered_orders = orders
                else:
                    filtered_orders = [
                        o for o in orders
                        if o['date_modified'] >= cutoff_date and o['status'] in ['processing', 'pending']
                    ]

                all_orders.extend(filtered_orders)

                # Se meno di per_page risultati, siamo alla fine
                if len(orders) < per_page:
                    break

                page += 1
                time.sleep(0.5)  # Rate limit gentile

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Errore recuperando ordini WooCommerce: {e}")
                raise

        logger.info(f"✅ Recuperati {len(all_orders)} ordini da WooCommerce")
        return all_orders

    def get_customer_by_id(self, customer_id: int) -> Dict:
        """Recupera dati cliente da WooCommerce"""
        try:
            response = self.session.get(
                f"{self.base_url}/customers/{customer_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore recuperando cliente {customer_id}: {e}")
            return {}


# ============================================================================
# NOCODB CLIENT
# ============================================================================

class NocODBClient:
    """Client per interagire con NocoDB API v2"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Helper per fare richieste autenticate"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, timeout=10, **kwargs)

            if response.status_code == 401:
                raise ValueError("Token NocoDB non valido o scaduto")

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore NocoDB ({method} {endpoint}): {e}")
            raise

    def get_table_records(self, table_id: str, filters: str = None, limit: int = 1000) -> List[Dict]:
        """
        Recupera record da una tabella NocoDB.

        Args:
            table_id: ID della tabella
            filters: Query filter in formato NocoDB
            limit: Numero massimo di record

        Returns:
            Lista di record
        """
        params = {'limit': limit}
        if filters:
            params['where'] = filters

        try:
            result = self._request('GET', f'/tables/{table_id}/records', params=params)
            return result.get('list', [])
        except Exception as e:
            logger.warning(f"⚠️ Errore nel recupero record da {table_id}: {e}")
            return []

    def create_record(self, table_id: str, data: Dict) -> Optional[Dict]:
        """Crea un nuovo record in NocoDB"""
        try:
            result = self._request('POST', f'/tables/{table_id}/records', json=data)
            logger.debug(f"✅ Record creato in {table_id}: {result.get('Id', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"❌ Errore creando record in {table_id}: {e}")
            return None

    def update_record(self, table_id: str, record_id: str, data: Dict) -> Optional[Dict]:
        """Aggiorna un record in NocoDB"""
        try:
            result = self._request('PATCH', f'/tables/{table_id}/records/{record_id}', json=data)
            logger.debug(f"✅ Record {record_id} aggiornato in {table_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Errore aggiornando record {record_id} in {table_id}: {e}")
            return None

    def get_record_by_email(self, table_id: str, email: str) -> Optional[Dict]:
        """Trova un record cliente per email"""
        try:
            records = self.get_table_records(table_id, filters=f"(Email,eq,{email})")
            return records[0] if records else None
        except Exception as e:
            logger.warning(f"⚠️ Errore cercando cliente con email {email}: {e}")
            return None

    def get_record_by_field(self, table_id: str, field: str, value: Any) -> Optional[Dict]:
        """Trova un record per un campo specifico"""
        try:
            records = self.get_table_records(table_id, filters=f"({field},eq,{value})")
            return records[0] if records else None
        except Exception as e:
            logger.warning(f"⚠️ Errore cercando {field}={value} in {table_id}: {e}")
            return None


# ============================================================================
# LOGICA DI SYNC
# ============================================================================

class WCNocODBSyncer:
    """Orchestrator per la sincronizzazione WooCommerce ↔ NocoDB"""

    def __init__(self, config: Dict):
        self.config = config
        self.wc = WooCommerceClient(
            config['woocommerce']['store_url'],
            config['woocommerce']['consumer_key'],
            config['woocommerce']['consumer_secret']
        )
        self.noco = NocODBClient(
            config['nocodb']['api_url'],
            config['nocodb']['api_token']
        )

        self.stats = {
            'clienti_nuovi': 0,
            'clienti_aggiornati': 0,
            'ordini_nuovi': 0,
            'ordini_aggiornati': 0,
            'errori': 0
        }

    def sync_clienti(self, wc_orders: List[Dict]):
        """Sincronizza la tabella Clienti da WooCommerce"""
        logger.info("👥 Sincronizzando clienti...")

        clienti_da_sync = {}

        # Estrai dati clienti dagli ordini
        for order in wc_orders:
            if not order.get('billing'):
                continue

            email = order['billing'].get('email', '').lower().strip()
            if not email:
                continue

            # Aggregazione intelligente per cliente
            if email not in clienti_da_sync:
                first_name = order['billing'].get('first_name', '')
                last_name = order['billing'].get('last_name', '')
                name = f"{first_name} {last_name}".strip()

                clienti_da_sync[email] = {
                    'Email': email,
                    'Name': name,
                    'Username': email,
                    'Phone (Billing)': order['billing'].get('phone', ''),
                    'Country / Region': order['billing'].get('country', ''),
                    'City': order['billing'].get('city', ''),
                    'Postal Code': order['billing'].get('postcode', ''),
                    'Orders': 0,
                    'Total Spend': 0.0,
                    'Last Active': datetime.utcnow().isoformat()
                }

            # Aggregazione
            clienti_da_sync[email]['Orders'] = clienti_da_sync[email].get('Orders', 0) + 1
            clienti_da_sync[email]['Total Spend'] = clienti_da_sync[email].get('Total Spend', 0.0) + float(order.get('total', 0))

        logger.info(f"📊 Trovati {len(clienti_da_sync)} clienti unici")

        # Sync in NocoDB
        table_id = self.config['nocodb']['table_ids']['clienti']

        for email, cliente_data in clienti_da_sync.items():
            try:
                # Cerca cliente esistente per email
                existing = self.noco.get_record_by_email(table_id, email)
                time.sleep(0.2)  # Rate limiting per NocoDB (200ms)

                if existing:
                    # UPDATE: aggiorna dati
                    self.noco.update_record(table_id, existing['Id'], cliente_data)
                    self.stats['clienti_aggiornati'] += 1
                else:
                    # INSERT: crea nuovo
                    self.noco.create_record(table_id, cliente_data)
                    self.stats['clienti_nuovi'] += 1

                time.sleep(0.2)  # Rate limiting per NocoDB (200ms)

            except Exception as e:
                logger.error(f"❌ Errore sincronizzando cliente {email}: {e}")
                self.stats['errori'] += 1

    def sync_ordini(self, wc_orders: List[Dict]):
        """Sincronizza la tabella Ordini da WooCommerce"""
        logger.info("📋 Sincronizzando ordini...")

        table_id = self.config['nocodb']['table_ids']['ordini']
        clienti_table_id = self.config['nocodb']['table_ids']['clienti']

        # Traccia ordini già sincronizzati (per evitare duplicati bundle)
        processed_order_ids = set()

        for order in wc_orders:
            try:
                order_id = str(order.get('id'))
                email = order['billing'].get('email', '').lower().strip()

                if not email or not order_id:
                    continue

                # Skip se ordine è già stato sincronizzato (evita duplicati bundle)
                if order_id in processed_order_ids:
                    logger.debug(f"⏭️ Ordine {order_id} già sincronizzato (bundle child), skip")
                    continue

                processed_order_ids.add(order_id)

                # Estrai dati ordine (mapping ai campi reali di NocoDB)
                ordine_data = {
                    'Order Number': order_id,
                    'Order Status': order.get('status', 'pending').capitalize(),
                    'Order Date': order.get('date_created', ''),
                    'Order Total Amount': float(order.get('total', 0)),
                    'Payment Method Title': order.get('payment_method_title', ''),
                    'Customer Note': order.get('customer_note', ''),
                    'Email (Billing)': email,
                    'First Name (Billing)': order['billing'].get('first_name', ''),
                    'Last Name (Billing)': order['billing'].get('last_name', ''),
                    'Phone (Billing)': order['billing'].get('phone', ''),
                    'Country Code (Billing)': order['billing'].get('country', ''),
                    'City (Billing)': order['billing'].get('city', ''),
                    'Address 1&2 (Billing)': order['billing'].get('address_1', ''),
                    'Postcode (Billing)': order['billing'].get('postcode', '')
                }

                # Estrai nome evento dal primo prodotto
                if order.get('line_items'):
                    ordine_data['Item Name'] = order['line_items'][0].get('name', '')
                    ordine_data['Quantity (- Refund)'] = order['line_items'][0].get('quantity', 1)
                    ordine_data['Item Cost'] = float(order['line_items'][0].get('total', 0))

                # Cerca ordine esistente per Order Number
                existing = self.noco.get_record_by_field(table_id, 'Order Number', order_id)
                time.sleep(0.2)  # Rate limiting per NocoDB (200ms)

                if existing:
                    # Se ordine è "completed" o "cancelled", non aggiornare più (frozen)
                    if existing.get('Order Status') in ['Completed', 'Cancelled']:
                        logger.info(f"❄️ Ordine {order_id} è frozen ({existing.get('Order Status')}), skip")
                        continue

                    # UPDATE se lo stato è cambiato
                    if existing.get('Order Status') != ordine_data['Order Status']:
                        self.noco.update_record(table_id, existing['Id'], ordine_data)
                        self.stats['ordini_aggiornati'] += 1
                        logger.info(f"🔄 Ordine {order_id}: {existing.get('Order Status')} → {ordine_data['Order Status']}")
                        time.sleep(0.2)  # Rate limiting per NocoDB (200ms)
                else:
                    # INSERT nuovo ordine
                    self.noco.create_record(table_id, ordine_data)
                    self.stats['ordini_nuovi'] += 1
                    time.sleep(0.2)  # Rate limiting per NocoDB (200ms)

            except Exception as e:
                logger.error(f"❌ Errore sincronizzando ordine {order.get('id')}: {e}")
                self.stats['errori'] += 1

    def run(self, full_sync: bool = False):
        """
        Esegui la sincronizzazione completa.

        Args:
            full_sync: Se True, scarica tutti gli ordini. Se False, ultimi 7 giorni.
        """
        start_time = datetime.utcnow()
        logger.info("=" * 70)
        logger.info("🚀 Avviando sync WooCommerce → NocoDB")
        logger.info("=" * 70)

        try:
            # Logica intelligente: full sync una volta al giorno
            days_back = 1000 if full_sync else 7

            # Recupera ordini da WooCommerce
            wc_orders = self.wc.get_orders(days_back=days_back)

            if not wc_orders:
                logger.info("ℹ️ Nessun ordine da sincronizzare")
                return self._print_summary(start_time)

            logger.info(f"📦 Trovati {len(wc_orders)} ordini processing da WooCommerce")

            # Sync clienti e ordini
            self.sync_clienti(wc_orders)
            self.sync_ordini(wc_orders)

            self._print_summary(start_time)

        except Exception as e:
            logger.error(f"❌ ERRORE CRITICO: {e}", exc_info=True)
            logger.info("STATUS: ❌ ERRORE")
            sys.exit(1)

    def _print_summary(self, start_time: datetime):
        """Stampa un riepilogo della sincronizzazione"""
        duration = (datetime.utcnow() - start_time).total_seconds()

        logger.info("=" * 70)
        logger.info("✨ Sync completato!")
        logger.info(f"👥 Clienti: {self.stats['clienti_nuovi']} nuovi, {self.stats['clienti_aggiornati']} aggiornati")
        logger.info(f"📋 Ordini: {self.stats['ordini_nuovi']} nuovi, {self.stats['ordini_aggiornati']} aggiornati")
        logger.info(f"⏱️ Durata: {duration:.1f}s")

        if self.stats['errori'] > 0:
            logger.warning(f"⚠️ Errori durante sync: {self.stats['errori']}")
            logger.info("STATUS: ⚠️ PARTIAL")
        else:
            logger.info("STATUS: ✅ OK")


# ============================================================================
# MAIN
# ============================================================================

def load_config(config_path: str = None) -> Dict:
    """Carica configurazione da file JSON o variabili ambiente"""

    # Path di default
    if not config_path:
        config_path = os.path.expanduser('~/.wc-nocodb-sync.json')

    # Prova a caricare da file
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Errore caricando config da {config_path}: {e}")

    # Fallback a variabili ambiente
    logger.warning("⚠️ File config non trovato, usando variabili ambiente...")

    return {
        'woocommerce': {
            'store_url': os.getenv('WC_STORE_URL'),
            'consumer_key': os.getenv('WC_CONSUMER_KEY'),
            'consumer_secret': os.getenv('WC_CONSUMER_SECRET')
        },
        'nocodb': {
            'api_url': os.getenv('NOCODB_API_URL', 'https://app.nocodb.com/api/v2'),
            'api_token': os.getenv('NOCODB_API_TOKEN'),
            'table_ids': {
                'clienti': os.getenv('NOCODB_TABLE_CLIENTI'),
                'ordini': os.getenv('NOCODB_TABLE_ORDINI')
            }
        }
    }


def main():
    """Punto di ingresso principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Sincronizza ordini WooCommerce a NocoDB'
    )
    parser.add_argument(
        '-c', '--config',
        help='Percorso file configurazione JSON',
        default=os.path.expanduser('~/.wc-nocodb-sync.json')
    )
    parser.add_argument(
        '--full-sync',
        action='store_true',
        help='Scarica tutti gli ordini (invece di ultimi 7 giorni)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Livello di logging'
    )

    args = parser.parse_args()

    # Configura logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Carica configurazione
    config = load_config(args.config)

    # Valida configurazione
    required_fields = [
        'woocommerce.store_url',
        'woocommerce.consumer_key',
        'woocommerce.consumer_secret',
        'nocodb.api_token',
        'nocodb.table_ids.clienti',
        'nocodb.table_ids.ordini'
    ]

    for field in required_fields:
        keys = field.split('.')
        val = config
        for key in keys:
            val = val.get(key) if isinstance(val, dict) else None

        if not val:
            logger.error(f"❌ Configurazione mancante: {field}")
            sys.exit(1)

    # Esegui sync
    syncer = WCNocODBSyncer(config)
    syncer.run(full_sync=args.full_sync)


if __name__ == '__main__':
    main()
