-- #############################################
-- TABLE: Users
-- #############################################
CREATE TYPE user_role AS ENUM ('SUPERADMIN', 'STAFF', 'GUEST');

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL,
    username VARCHAR(64) UNIQUE NOT NULL,
    salted_password VARCHAR(128) NOT NULL,
    user_role user_role NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- #############################################
-- TABLE: Boards
-- #############################################

CREATE TABLE boards (
	board_id BIGSERIAL PRIMARY KEY NOT NULL,
	board_owner BIGINT NOT NULL,
	board_name VARCHAR(256) UNIQUE NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT foreign_key_board_owner FOREIGN KEY (board_owner) REFERENCES users(user_id)
);

CREATE TYPE board_moderator_status AS ENUM ('CONFIRMED', 'PENDING');

CREATE TABLE boards_moderators (
	boards_moderator_id BIGSERIAL PRIMARY KEY NOT NULL,
	board_id BIGINT NOT NULL,
	user_id BIGINT NOT NULL,
	status board_moderator_status NOT NULL,
	date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE(board_id, user_id),
    CONSTRAINT foreign_key_board_id FOREIGN KEY (board_id) REFERENCES boards(board_id),
    CONSTRAINT foreign_key_user_id FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_boards_moderators_board_id_status ON boards_moderators(board_id, status);
CREATE INDEX idx_boards_moderators_user_id_status ON boards_moderators(user_id, status);


-- #############################################
-- TABLE: Posts
-- #############################################
CREATE TABLE posts (
    post_id BIGSERIAL PRIMARY KEY NOT NULL,
    board_id BIGINT NOT NULL,
    post_owner BIGINT NOT NULL,
	post_title VARCHAR(256) NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT foreign_key_board_id FOREIGN KEY (board_id) REFERENCES boards(board_id),
    CONSTRAINT foreign_key_post_owner FOREIGN KEY (post_owner) REFERENCES users(user_id)
);

CREATE INDEX idx_posts_board_id_date_created ON posts(board_id, date_created);


-- #############################################
-- TABLE: Threads
-- #############################################
CREATE TABLE threads (
    thread_id BIGSERIAL PRIMARY KEY NOT NULL,
    post_id BIGINT NOT NULL,
    thread_owner BIGINT NOT NULL,
	thread_content TEXT NOT NULL,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT foreign_key_post_id FOREIGN KEY (post_id) REFERENCES posts(post_id),
    CONSTRAINT foreign_key_thread_owner FOREIGN KEY (thread_owner) REFERENCES users(user_id)
);

CREATE INDEX idx_threads_post_id ON threads(post_id, date_created);
