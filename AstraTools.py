
# Define the Tools and 
ASTRA_TOOLS = [{
    "name": "get_customer_feature",
    "description": "Given a customer_id and a feature, returns and information about the customer",
    "source": "REST",
    "table": "airlinecustomerfeaturestore",
    "params":  {
        "customer_id": {
            "type": str,
            "mandatory": True,
            "description": "The UUID that represents the customer"},
        "feature":  {
            "type": str,
            "mandatory": True,
            "description": "The information about the customer: date_of_birth, gender, has_TSA, meal_preference, miles, miles category, nationality"
        }
    },
    "options": {'page-size': 1,
                'fields': 'feature,value'}
}, {
    "name": "get_scheduled_flights",
    "description": "Returns information about scheduled flights considering conditions for arrivalAirport, departureAirport, departureDateTime. Consider Airport codes and Dates in ISO format",
    "source": "REST",
    "table": "airlinecustomerfeaturestore",
    "params": [{"customer_id": "string", "mandatory": True},
               {"feature": "string", "mandatory": True}],
    "options": {'page-size': 1,
                'fields': 'feature,value'}
}]
