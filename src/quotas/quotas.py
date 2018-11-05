from functools import wraps
from pyinfraboxutils import dbpool

def check_quotas(name, object_id):

    quota_value = get_quota_value(name, object_id)

    current_data = get_current_data(object_id)

    #return
    return quota_value >= current_data

def get_quota_value(name, object_id="default_value"):

    db = dbpool.get()

    quota_value = db.execute_one("""
                    SELECT value FROM public.quotas WHERE name = %s AND object_id = %s
    """, [name, object_id])

    if quota_value == [] or quota_value is None:
        quota_value = db.execute_one("""
                    SELECT value FROM public.quotas WHERE name = %s AND object_id = 'default_value'
    """, [name])
    return quota_value[0]

#TODO
def get_current_data(name):
    pass
 