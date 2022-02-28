INSERT INTO users (user_id, email, username, salted_password, user_role) VALUES (1, 'admin@admin.com', 'key-admin', '$5$rounds=535000$DsM0iyY/z5QQBZsl$QnrFXh5a2Op4Py.S1Fd8tPFCBRlFaj1PfPtwa.sOkWB', 'SUPERADMIN');
INSERT INTO users (user_id, email, username, salted_password, user_role) VALUES (2, 'staff@admin.com', 'key-staff', '$5$rounds=535000$DsM0iyY/z5QQBZsl$QnrFXh5a2Op4Py.S1Fd8tPFCBRlFaj1PfPtwa.sOkWB', 'STAFF');
INSERT INTO users (user_id, email, username, salted_password, user_role) VALUES (3, 'guest@admin.com', 'key-guest', '$5$rounds=535000$DsM0iyY/z5QQBZsl$QnrFXh5a2Op4Py.S1Fd8tPFCBRlFaj1PfPtwa.sOkWB', 'GUEST');

INSERT INTO boards (board_id, board_owner, board_name) VALUES (1, 1, 'key-board');

INSERT INTO posts (post_id, board_id, post_owner, post_title) VALUES (1, 1, 1, 'key-post');

INSERT INTO threads (thread_id, post_id, thread_owner, thread_content) VALUES (1, 1, 1, 'thread content - blah blah');
