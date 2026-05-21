import csv
import collections

def format_currency(value):
    return f"${value:,.2f}"

def format_percent(value):
    return f"{value:.2%}"

BROAD_MARKET_SYMBOLS = {'SPY', 'VOO', 'IWM', 'QQQ', 'QQQM', 'QQQE', 'EFA'}

def analyze_positions(file_path, export_path='exposure_summary.csv'):
    symbol_data = collections.defaultdict(lambda: {"equity": 0.0, "option": 0.0, "description": "", "type": ""})
    broker_data = collections.defaultdict(lambda: collections.defaultdict(float))
    asset_type_data = collections.defaultdict(float)
    total_portfolio_value = 0.0

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                symbol = row['symbol']
                asset_type = row['asset_type']
                try:
                    market_value = float(row['market_value']) if row['market_value'] else 0.0
                except ValueError:
                    market_value = 0.0
                
                broker = row['broker']
                account = row['account']
                description = row['description']

                # Effective Asset Type for Broad Market
                effective_asset_type = asset_type
                if symbol in BROAD_MARKET_SYMBOLS and asset_type == 'Equity':
                    effective_asset_type = 'Broad Market'

                # Symbol View
                if asset_type == 'Equity':
                    symbol_data[symbol]['equity'] += market_value
                    symbol_data[symbol]['type'] = 'Broad Market' if symbol in BROAD_MARKET_SYMBOLS else 'Equity'
                    if not symbol_data[symbol]['description']:
                        symbol_data[symbol]['description'] = description
                elif asset_type == 'Option':
                    symbol_data[symbol]['option'] += market_value
                    if not symbol_data[symbol]['type']:
                        symbol_data[symbol]['type'] = 'Broad Market' if symbol in BROAD_MARKET_SYMBOLS else 'Equity'
                
                # Global total value includes everything
                total_portfolio_value += market_value

                # Broker/Account View
                broker_data[broker][account] += market_value

                # Asset Type View
                asset_type_data[effective_asset_type] += market_value

    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    # Process Symbol Report
    symbol_report = []
    for symbol, data in symbol_data.items():
        total = data['equity'] + data['option']
        if total != 0 or data['equity'] != 0 or data['option'] != 0:
            symbol_report.append({
                "symbol": symbol,
                "description": data['description'],
                "type": data['type'],
                "equity": data['equity'],
                "option": data['option'],
                "total": total
            })
    
    # Sort by total exposure descending
    symbol_report.sort(key=lambda x: x['total'], reverse=True)

    # --- Print Symbol Report ---
    print("\n" + "="*125)
    print(f"{'Rank':<5} {'Symbol':<10} {'Type':<15} {'Description':<30} {'Equity ($)':>15} {'Option ($)':>15} {'Total ($)':>15} {'% Port':>10}")
    print("-" * 125)
    for i, item in enumerate(symbol_report, 1):
        pct = item['total'] / total_portfolio_value if total_portfolio_value else 0
        desc = (item['description'][:27] + '...') if len(item['description']) > 30 else item['description']
        print(f"{i:<5} {item['symbol']:<10} {item['type']:<15} {desc:<30} {format_currency(item['equity']):>15} {format_currency(item['option']):>15} {format_currency(item['total']):>15} {format_percent(pct):>10}")

    # --- Export to CSV ---
    try:
        with open(export_path, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['rank', 'symbol', 'type', 'description', 'equity_exposure', 'option_exposure', 'total_exposure', 'percent_portfolio']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, item in enumerate(symbol_report, 1):
                pct = item['total'] / total_portfolio_value if total_portfolio_value else 0
                writer.writerow({
                    'rank': i,
                    'symbol': item['symbol'],
                    'type': item['type'],
                    'description': item['description'],
                    'equity_exposure': round(item['equity'], 2),
                    'option_exposure': round(item['option'], 2),
                    'total_exposure': round(item['total'], 2),
                    'percent_portfolio': format_percent(pct)
                })
        print(f"\nSuccessfully exported summary to {export_path}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")

    # --- Print Broker/Account Summary ---
    print("\n" + "="*95)
    print("BROKER & ACCOUNT SUMMARY")
    print("-" * 95)
    for broker, accounts in broker_data.items():
        broker_total = sum(accounts.values())
        print(f"Broker: {broker} (Total: {format_currency(broker_total)})")
        for account, value in accounts.items():
            acc_pct = value / total_portfolio_value if total_portfolio_value else 0
            print(f"  - Account: {account:<20} {format_currency(value):>15} ({format_percent(acc_pct)})")

    # --- Print Asset Type Summary ---
    print("\n" + "="*95)
    print("ASSET TYPE SUMMARY")
    print("-" * 95)
    sorted_assets = sorted(asset_type_data.items(), key=lambda x: x[1], reverse=True)
    for asset_type, value in sorted_assets:
        asset_pct = value / total_portfolio_value if total_portfolio_value else 0
        print(f"{asset_type:<15}: {format_currency(value):>15} ({format_percent(asset_pct)})")

    print("-" * 95)
    print(f"{'TOTAL PORTFOLIO':<15}: {format_currency(total_portfolio_value):>15}")
    print("="*95 + "\n")

if __name__ == "__main__":
    analyze_positions('positions.csv')
