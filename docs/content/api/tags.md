---
title: "Tags"
description: "List built-in and task-created tags."
---

## List tags

`GET /api/tags`

Returns an array of tag names. It always includes the built-in tags `School`, `Work`, `House`, `Personal`, and `Other`, plus any additional tag values currently used by tasks.

```sh
curl "http://127.0.0.1:8000/api/tags"
```

Tags are created implicitly when a task is created or updated with a tag value. There is no separate tag creation or deletion endpoint; a custom tag disappears from the returned list when no tasks use it.
