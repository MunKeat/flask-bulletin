from flask import Flask

app = Flask(__name__) 


@app.route("/", methods=["GET"])
def home():
    return "Hello, World!"


@app.route("/signup", methods=["POST"])
def signup():
	pass


@app.route("/login", methods=["POST"])
def login():
	pass


@app.route("/avatar/<user_id>", methods=["GET"])
def avatar():
	pass



@app.route("/boards/list", methods=["GET"])
def boards_list():
	pass

@app.route("/board/create", methods=["POST"])
def board_create():
	pass

@app.route("/board/<board_id>/read/", methods=["GET"])
def board_read():
	pass

@app.route("/board/<board_id>/edit", methods=["PUT"])
def board_edit():
	pass

@app.route("/board/<board_id>/delete", methods=["DELETE"])
def board_delete():
	pass




@app.route("/board/<board_id>/moderate/<user_id>", methods=["POST"])
def board_moderation_invite():
	pass

@app.route("/board/<board_id>/moderate/list", methods=["GET"])
def board_moderation_list_invites():
	pass

@app.route("/board/<board_id>/moderate/revoke", methods=["DELETE"])
def board_moderation_revoke_invites():
	pass


@app.route("/board/<board_id>/moderate/accept", methods=["POST"])
def board_moderation_accept():
	pass



@app.route("/board/<board_id>/threads/list", methods=["GET"])
def thread_list():
	pass

@app.route("/board/<board_id>/thread/create", methods=["POST"])
def thread_create():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/read", methods=["POST"])
def thread_read():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/edit", methods=["PUT"])
def thread_edit():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/delete", methods=["DELETE"])
def thread_delete():
	pass



@app.route("/board/<board_id>/thread/<thread_id>/post/create", methods=["POST"])
def post_create():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/post/read", methods=["POST"])
def post_read():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/post/edit", methods=["PUT"])
def post_edit():
	pass

@app.route("/board/<board_id>/thread/<thread_id>/post/delete", methods=["DELETE"])
def post_delete():
	pass

