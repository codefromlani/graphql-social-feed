### OVERVIEW
A GraphQL-based backend for managing social media posts and interactions. Built with Django, PostgreSQL, and GraphQL, this project provides flexible APIs for creating, querying, and managing posts, comments, likes, shares, and follows.

## Local Setup:
1. Clone the Repository

```python
   git clone https://github.com/codefromlani/graphql-social-feed.git
   cd graphql-social-feed
```

2. Create Virtual Environment
#### Windows

```python
   python -m venv venv
   venv\Scripts\activate
```

#### Linux/Mac

```python
   python3 -m venv venv
   source venv/bin/activate
```
3. Install Dependencies

```python
   pip install -r requirements.txt
```

4. Set Up Environment Variables
#### Copy `.env.example` :

```python
   cp .env.example .env
```

5. Set Up PostgreSQL Database
#### Access PostgreSQL

```python
   psql -U postgres
```

#### Create database

```python
   CREATE DATABASE social_feed_db;
```

#### Exit PostgreSQL

```python
   \q
```

6. Run Migrations

```python
   python manage.py migrate
```

7. Create Superuser

```python
   python manage.py createsuperuser
```

8. Run Development Server

```python
   python manage.py runserver
```

The application will be available at:

- GraphQL API: `http://127.0.0.1:8000/graphql`
- jango Admin: `http://127.0.0.1:8000/admin/`

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

### Indexes & performance notes

- Posts: index (author, -created_at), index (-created_at).

- Comments: index (post, -created_at), index (author).

- Likes/Shares: indexes on (post) and (user). Unique constraint prevents duplicates.

- Follows: index on follower and followed for fast lookups.

### GraphQL API (Graphene)

Root schema provides:

- Queries: post, globalFeed, authorFeed, comments, replies, likes, shares, followers, following

Mutations:

- Posts: createPost, updatePost, deletePost (soft), likePost, unlikePost, sharePost, unsharePost

- Comments: createComment, deleteComment

- Follows: followUser, unfollowUser

- Auth: signup, tokenAuth, refreshToken, verifyToken (from graphql_jwt)

