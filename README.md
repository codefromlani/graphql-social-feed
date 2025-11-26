# OVERVIEW

### Goal
A high-performance social feed backend that demonstrates deep backend engineering skills — GraphQL API, efficient data loading, caching, async jobs, real-time updates, and production deployment.

## Core stack:

- Backend: Django, Graphene (GraphQL), Django Channels

- Database: PostgreSQL

- Cache & broker: Redis

- Async tasks: Celery

- Auth: JWT 

- Containerization: Docker + Docker Compose

- Testing & CI: pytest, GitHub Actions

### Key Entities

- USERS (apps.accounts.User)

   - id: UUID PK

   - username: varchar unique

   - email: varchar unique

   - password (hashed)

   - is_active, is_staff

   - created_at, last_login

- POSTS (apps.posts.Post)

   - id: UUID PK

   - author_id -> users.id (FK)

   - content: text

   - language: varchar(10)

   - is_private: boolean

   - visibility: varchar(20) [public/followers/private]

   - reply_to_post_id -> posts.id (FK nullable)

   - created_at, updated_at, deleted_at (soft delete)

- COMMENTS (apps.posts.Comment)

   - id: UUID PK

   - post_id -> posts.id (FK)

   - author_id -> users.id (FK)

   - content: text

   - parent_comment_id -> comments.id (FK)

   - created_at, deleted_at

- LIKES (apps.posts.Like)

   - id: BIGSERIAL PK

   - user_id -> users.id (FK)

   - post_id -> posts.id (FK)

   - reaction: varchar(20)

   - created_at

   - UNIQUE(user_id, post_id)

- SHARES (apps.posts.Share)

   - id: BIGSERIAL PK

   - user_id -> users.id (FK)

   - post_id -> posts.id (FK)

   - created_at

   - UNIQUE(user_id, post_id)

- FOLLOWS (apps.social.Follow)

   - id: BIGSERIAL PK

   - follower_id -> users.id (FK)

   - followed_id -> users.id (FK)

   - created_at

   - UNIQUE(follower_id, followed_id)

   - CHECK: follower != followed

- NOTIFICATIONS (apps.social.Notification)

   - id: BIGSERIAL PK

   - recipient_id -> users.id (FK)

   - actor_id -> users.id (FK nullable)

   - verb: varchar(50) ('liked', 'commented', 'followed', 'shared', etc.)

   - target_type: varchar(50) nullable

   - target_id: UUID nullable

   - data: JSONB (metadata)

   - is_read: boolean default false

   - created_at: timestamp

### Indexes & performance notes

- Posts: index (author, -created_at), index (-created_at).

- Comments: index (post, -created_at), index (author).

- Likes/Shares: indexes on (post) and (user). Unique constraint prevents duplicates.

- Follows: index on follower and followed for fast lookups.

- Notifications: index (recipient, is_read, -created_at) for unread query + pagination.

### GraphQL API (Graphene)

Root schema provides:

- Queries: post, globalFeed, authorFeed, comments, replies, likes, shares, followers, following, notifications

Mutations:

- Posts: createPost, updatePost, deletePost (soft), likePost, unlikePost, sharePost, unsharePost

- Comments: createComment, deleteComment

- Follows: followUser, unfollowUser

- Notifications: markNotificationRead, markAllRead

- Auth: signup, tokenAuth, refreshToken, verifyToken (from graphql_jwt)

Subscriptions (via WebSockets):

- notificationAdded (push new notifications in real time to recipient)

### Notification flow (event)

Example: user A likes post P owned by user B

A executes likePost(postId=P) mutation (GraphQL, authenticated)

Mutation creates/updates Like DB row

Mutation calls create_notification_task.delay(recipient_id=B, actor_id=A, verb="liked", target_type="post", target_id=P, data={...})

Celery worker runs create_notification_task:

creates Notification DB row (recipient=B)

calls push_notification_to_user(notification) which sends payload to channels group user_notifications:{B}

If user B has an open GraphQL subscription (via channels_graphql_ws) they immediately receive the notification payload.

The client can then show a toast + update in-app notification list and update unread count.

### Realtime implementation details

- Channel layer: Redis (channels_redis)

- Broker: Redis (Celery)

- GraphQL subscriptions: channels_graphql_ws library with a GraphQL WebSocket consumer

- Group naming: user_notifications:{user_id}

- Publishing: Celery task writes DB record and publishes to Channel Layer group

- Client: opens WebSocket to /subscriptions/ and subscribes to notificationAdded for the current user.

Example GraphQL subscription (client)

Client opens WS to: ws://HOST/subscriptions/
Sends GraphQL subscription:

subscription {
  notificationAdded {
    notification {
      id
      verb
      actor { id username }
      data
      isRead
      createdAt
    }
  }
}

Server only publishes notifications to the group matching the current user's id.

### Security & scaling considerations

Authenticate websocket connections (AuthMiddlewareStack) — ensure tokens are validated.

Rate-limit notification creation if needed to avoid spam.

For very large traffic, consider a dedicated events/streaming service (Kafka) and eventual read models (materialized tables) for feeds/notifications.

Retention: consider purging notifications older than X months or archiving.

Use Redis cluster / SQS + Workers to scale Celery and channel layer.
