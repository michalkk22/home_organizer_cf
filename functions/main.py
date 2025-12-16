from firebase_functions import firestore_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore

set_global_options(max_instances=2)

initialize_app()

ACCEPTED = "accepted"
PENDING = "pending"
FAILED = "failed"

def get_db():
    return firestore.client()

@firestore_fn.on_document_updated(document="invitations/{inviteId}")
def on_invite_used(event: firestore_fn.Event):
    db = get_db()
    before = event.data.before.to_dict()
    after = event.data.after.to_dict()

    # detect newly added user
    new_users = set(after["usedBy"]) - set(before["usedBy"])
    if not new_users:
        return

    uid = list(new_users)[0]
    home_id = after["homeId"]
    inv_ref = event.data.reference

    try:
        # update status to pending
        inv_ref.update({
            f"status.{uid}": PENDING
        })

        # add user to group
        db.collection("homes").document(home_id).update({
            "members": firestore.ArrayUnion([uid])
        })

        # create permissions doc
        db.collection("homes").document(home_id) \
        .collection("permissions").document(uid).set({
            "isOwner": False,
        })

        # update status to accepted
        inv_ref.update({
            f"status.{uid}": ACCEPTED
        })

    except Exception as e:
        inv_ref.update({
            f"status.{uid}": FAILED,
            f"errors.{uid}": str(e),
        })