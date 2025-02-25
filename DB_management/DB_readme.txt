DATABASE TYPE RULES:

Users Table

id: uuid (auto‐generated using gen_random_uuid())
discord_id: text, NOT NULL, UNIQUE
username: text (nullable)
created_at: timestamp with time zone, defaults to now()
Recommended Items Table

id: uuid (auto‐generated)
item_name: text, NOT NULL
vendor: text, NOT NULL
link: text, NOT NULL
price: numeric, NOT NULL
metadata: jsonb (used for any additional data)
created_at: timestamp with time zone, defaults to now()
Queries Table

id: uuid (auto‐generated)
user_id: uuid, references users(id) with ON DELETE CASCADE
query_type: text, NOT NULL, must be either 'prompted' or 'unprompted'
raw_query: text (used for prompted queries; can be NULL)
interpreted_query: jsonb, NOT NULL
recommended_item_id: uuid, references recommended_items(id) with ON DELETE SET NULL
created_at: timestamp with time zone, defaults to now()
Reactions Table

id: uuid (auto‐generated)
query_id: uuid, references queries(id) with ON DELETE CASCADE
reaction_type: text, NOT NULL, must be either 'wishlist' or 'dislike'
created_at: timestamp with time zone, defaults to now()
