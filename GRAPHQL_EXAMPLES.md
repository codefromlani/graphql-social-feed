## Signup

```python
mutation Register {
  signup(username: "alice", email: "alice@mail.com", password: "1234") {
    token
    user {
      id
      username
      email
    }
  }
}
```

## Login

```python
mutation Login {
  tokenAuth(username: "alice", password: "1234") {
    token
  }
}
```

## Me

### Add header
```python
{
  "Authorization": "JWT <token>"
}
```
Then
```python
query {
  me {
    id
    username
    email
  }
}
```

## CreatePost (requires authorization)

```python
mutation createPost {
  createPost(input: {content: "Hello world", language: "en", visibility: "public"}) {
    post {
      id
      content
      author { username id }
      createdAt
    }
  }
}
```
## UpdatePost (requires authorization)

```python
mutation updatePost {
  updatePost(input: {postId: "post_id", content: "Updated text"}) {
    post { id content updatedAt }
  }
}
```

## LikePost (requires authorization)

```python
mutation likePost {
  likePost(postId: "post_id") { like { id reaction user { id } } }
}
```

## Comment (requires authorization)

```python
mutation createComment {
  createComment(input: {
    postId: "post_id",
    content: "Nice post!"
  }) {
    comment {
      id
      content
      author { username }
      createdAt
    }
  }
}
```

## FetchFeed 

```python
query globalFeed {
  globalFeed(limit: 10, offset: 0) {
    total
    hasNext
    items {
      id
      content
      author { username }
      createdAt
    }
  }
}
```

## SharePost (requires authorization)

```python
mutation sharePost {
  sharePost(postId: "post_id") {
    share {
      id
      user { username }
      post { id }
      createdAt
    }
  }
}
```

## FollowAUser (requires authorization)

```python
mutation FollowUser {
  followUser(followedId: "user_id") {
    id
    follower { id username }
    followed { id username }
    createdAt
  }
}
```
