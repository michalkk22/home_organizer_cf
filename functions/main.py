from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app

set_global_options(max_instances=2)

initialize_app()

@firestore_fn.on_document_updated(document="invitations/{inviteId}")
def on_invite_used(event: firestore_fn.Event):
    before = event.data.before.to_dict()
    after = event.data.after.to_dict()

    # detect newly added user
    new_users = set(after["usedBy"]) - set(before["usedBy"])
    if not new_users:
        return

    uid = list(new_users)[0]
    home_id = after["homeId"]

    # add user to group
    db.collection("homes").document(home_id).update({
        "members": firestore.ArrayUnion([uid])
    })

    # create permissions doc
    db.collection("homes").document(home_id) \
      .collection("permissions").document(uid).set({
        "isOwner": False,
    })