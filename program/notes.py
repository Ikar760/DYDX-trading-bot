from datetime import datetime, timedelta
from func_utils import format_number
import time

from pprint import pprint

# Place market order
def place_market_order(client, market, side, size, price, reduce_only):

    # Get position ID (Market order in documentation)
    account_response = client.private.get_account()
    position_id = account_response.data["account"]["positionId"]

    # Get expiration time
    server_time = client.public.get_time()
    expiration = datetime.fromisoformat((server_time.data["iso"].replace("Z","")) + timedelta(seconds=70))

    # Place an order
    placed_order = client.private.create_order(
        position_id=position_id, # required for creating the order signature
        market=market,
        side="BUY",
        order_type="MARKET",
        post_only=False,
        size=size,
        price=price, #above current price
        limit_fee='0.015',
        expiration_epoch_seconds=expiration.timestamp(),
        time_in_force="FOK", #fill or kill
        reduce_only=reduce_only #changes the position from close to open
    )

    # Return result
    return placed_order.data


    

# Abort all positions
def abort_all_positions(client):
    
    # Cancel all orders
    client.private.cancel_all_orders()

    # Protect API
    time.sleep(0.5)

    # get mkt for ref of tick size
    markets = client.public.get_markets().data

    # Protect API
    time.sleep(0.5)

    # Get all open positions
    positions = client.private.get_positions(status="OPEN")
    all_positions = positions.data["positions"]
    
    
    # Handle open positions
    close_orders = []
    if len(all_positions) > 0:

        # Loop through each position
        for position in all_positions:

            # Determine market
            market = position["market"]

            # Determine Side
            side = "BUY"
            if position["side"] == "LONG":
                side = "SELL"

            
            # Get Price
            price = float(position["entryPrice"])
            accept_price = price * 1.7 if side == "BUY" else price * 0.3 #if price is 70% wrst than when opening position
            tick_size = markets["markets"][market]["tickSize"]
            accept_price = format_number(accept_price, tick_size)

            # Place order to close
            order = place_market_order (
                client,
                market,
                side,
                position["sumOpen"], # quantity we have
                accept_price,
                True
            )

            # Append the result
            close_orders.append(order)

            # Protect API
            time.sleep(0.2)

            # Return close orders
            return close_orders
