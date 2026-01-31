from decimal import Decimal
from posApp.models import StockEntry


def consume_fifo(product, store, qty):
    """
    Deduct from oldest StockEntry first
    """
    remaining = Decimal(qty)

    entries = StockEntry.objects.filter(
        product=product,
        store=store,
        remaining_quantity__gt=0
    ).order_by("date_received")

    for entry in entries:
        if remaining <= 0:
            break

        take = min(entry.remaining_quantity, remaining)
        entry.remaining_quantity -= take
        entry.save()

        remaining -= take

    if remaining > 0:
        raise Exception(f"Not enough stock for {product.name}")
