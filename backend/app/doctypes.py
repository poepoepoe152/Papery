"""Document-type definitions and the field catalog (schema-driven).

The architecture treats document types as configuration. This module holds:
- CLASSIFICATION_RULES: keyword anchors used to detect document type.
- FIELD_CATALOG: every extractable field with its label aliases, severity,
  and value kind (drives normalization + regex extraction).
"""

# Most specific patterns first.
CLASSIFICATION_RULES = [
    ("DRAFT_BL", ["draft bill of lading", "draft b/l", "draft bl"]),
    ("SEA_WAYBILL", ["sea waybill", "seaway bill", "waybill"]),
    ("FINAL_BL", ["bill of lading", "b/l no", "bill of  lading"]),
    ("BOOKING", ["booking confirmation", "booking note", "booking no", "booking number"]),
    ("SHIPPING_INSTRUCTION", ["shipping instruction", "shipping instructions"]),
    ("COMMERCIAL_INVOICE", ["commercial invoice"]),
    ("PACKING_LIST", ["packing list"]),
    ("DELIVERY_ORDER", ["delivery order"]),
    ("PURCHASE_ORDER", ["purchase order", "p.o. no", "po number"]),
    ("FREIGHT_REQUEST", ["freight request"]),
    ("CONTRACT", ["contract", "agreement"]),
    # multilingual anchors prove the schema-driven design: adding a language
    # is a config change (fr: facture, de: rechnung, es: factura)
    ("INVOICE", ["invoice", "facture", "rechnung", "factura"]),
]

DOC_TYPE_LABELS = {
    "DRAFT_BL": "Draft Bill of Lading",
    "FINAL_BL": "Final Bill of Lading",
    "SEA_WAYBILL": "Sea Waybill",
    "BOOKING": "Booking Confirmation",
    "SHIPPING_INSTRUCTION": "Shipping Instruction",
    "COMMERCIAL_INVOICE": "Commercial Invoice",
    "INVOICE": "Invoice",
    "PACKING_LIST": "Packing List",
    "DELIVERY_ORDER": "Delivery Order",
    "PURCHASE_ORDER": "Purchase Order",
    "FREIGHT_REQUEST": "Freight Request",
    "CONTRACT": "Contract",
    "UNKNOWN": "Unknown",
}

# kind: id | text | number | date | container
FIELD_CATALOG = {
    "booking_number": {
        "label": "Booking Number", "severity": "CRITICAL", "kind": "id",
        "aliases": ["booking number", "booking no", "booking ref", "bkg no", "booking"],
    },
    "bl_number": {
        "label": "B/L Number", "severity": "CRITICAL", "kind": "id",
        "aliases": ["bill of lading no", "b/l no", "bl no", "bl number", "b/l number", "document no"],
    },
    "invoice_number": {
        "label": "Invoice Number", "severity": "MAJOR", "kind": "id",
        "aliases": ["invoice no", "invoice number", "inv no", "invoice #",
                    "facture n°", "rechnung nr", "factura no"],
    },
    "shipper": {
        "label": "Shipper", "severity": "CRITICAL", "kind": "text",
        "aliases": ["shipper", "exporter"],
    },
    "consignee": {
        "label": "Consignee", "severity": "CRITICAL", "kind": "text",
        "aliases": ["consignee"],
    },
    "notify_party": {
        "label": "Notify Party", "severity": "MAJOR", "kind": "text",
        "aliases": ["notify party", "notify"],
    },
    "commodity": {
        "label": "Commodity", "severity": "MAJOR", "kind": "text",
        "aliases": ["commodity", "description of goods", "goods description", "description"],
    },
    "container_number": {
        "label": "Container Number", "severity": "CRITICAL", "kind": "container",
        "multi": True,  # a shipment often has several containers
        "aliases": ["container no", "container number", "container/seal", "container"],
    },
    "seal_number": {
        "label": "Seal Number", "severity": "CRITICAL", "kind": "id",
        "multi": True,
        "aliases": ["seal no", "seal number", "seal"],
    },
    "gross_weight": {
        "label": "Gross Weight", "severity": "CRITICAL", "kind": "number",
        "aliases": ["gross weight", "g.w.", "gross wt", "gw"],
    },
    "net_weight": {
        "label": "Net Weight", "severity": "MAJOR", "kind": "number",
        "aliases": ["net weight", "n.w.", "net wt", "nw"],
    },
    "measurement_cbm": {
        "label": "Measurement (CBM)", "severity": "MAJOR", "kind": "number",
        "aliases": ["measurement", "cbm", "volume", "m3"],
    },
    "package_count": {
        "label": "Package Count", "severity": "MAJOR", "kind": "number",
        "aliases": ["number of packages", "no of packages", "packages", "pkgs", "package", "cartons", "carton", "quantity"],
    },
    "carrier": {
        "label": "Carrier", "severity": "MAJOR", "kind": "text",
        "aliases": ["carrier", "carrier name", "shipping line"],
    },
    "vessel": {
        "label": "Vessel", "severity": "CRITICAL", "kind": "text",
        "aliases": ["mother vessel", "ocean vessel", "vessel name", "vessel"],
    },
    "feeder_vessel": {
        "label": "Feeder Vessel", "severity": "MAJOR", "kind": "text",
        "aliases": ["feeder vessel", "feeder"],
    },
    "voyage": {
        "label": "Voyage", "severity": "CRITICAL", "kind": "id",
        "aliases": ["voyage no", "voyage", "voy no", "voy"],
    },
    "eta": {
        "label": "ETA", "severity": "CRITICAL", "kind": "date",
        "aliases": ["eta", "estimated arrival", "arrival date"],
    },
    "etd": {
        "label": "ETD", "severity": "CRITICAL", "kind": "date",
        "aliases": ["etd", "estimated departure", "departure date"],
    },
    "port_of_loading": {
        "label": "Port of Loading", "severity": "CRITICAL", "kind": "text",
        "aliases": ["port of loading", "pol", "loading port"],
    },
    "port_of_discharge": {
        "label": "Port of Discharge", "severity": "CRITICAL", "kind": "text",
        "aliases": ["port of discharge", "pod", "discharge port"],
    },
    "place_of_receipt": {
        "label": "Place of Receipt", "severity": "MAJOR", "kind": "text",
        "aliases": ["place of receipt", "por"],
    },
    "place_of_delivery": {
        "label": "Place of Delivery", "severity": "MAJOR", "kind": "text",
        "aliases": ["place of delivery", "final destination"],
    },
    "freight_term": {
        "label": "Freight Term", "severity": "MINOR", "kind": "text",
        "aliases": ["freight term", "freight terms", "freight", "payment term"],
    },
    "temperature": {
        "label": "Temperature", "severity": "MAJOR", "kind": "text",
        "aliases": ["temperature", "reefer temp", "set temp", "temp"],
    },
    "original_bl_count": {
        "label": "Original BL Count", "severity": "MINOR", "kind": "number",
        "aliases": ["number of originals", "no of original", "original bl", "originals"],
    },
}
