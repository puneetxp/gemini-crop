-- Browser web push subscriptions: one row per browser endpoint, owned by a user.

CREATE TABLE IF NOT EXISTS push_subscriptions (
    "id" BIGSERIAL PRIMARY KEY,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "enable" SMALLINT NOT NULL DEFAULT 1,
    "user_id" BIGINT NOT NULL,
    "endpoint" TEXT NOT NULL, -- Browser push service URL, unique per browser
    "p256dh" VARCHAR(255) NOT NULL,
    "auth" VARCHAR(255) NOT NULL,
    "user_agent" VARCHAR(512) NULL
);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions (user_id);
