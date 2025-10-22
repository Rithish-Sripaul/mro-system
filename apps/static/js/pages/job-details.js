const commentForm = document.getElementById('comment-form');
    const commentTextarea = document.getElementById('comment-textarea');
    const commentsListContainer = document.getElementById('comments-list-container');
    const commentCountSpan = document.getElementById('comment-count');
    
    // Get the job ID from the template
    const jobId = '{{ job._id | string }}';

    // --- 2. CORE FUNCTIONS ---

    /**
     * Fetches all comments and renders them
     */
    async function fetchAndRenderComments() {
      try {
        const response = await fetch(`/api/jobs/${jobId}/comments`);
        if (!response.ok) throw new Error('Failed to fetch comments');
        
        const comments = await response.json();
        
        // Update count
        commentCountSpan.textContent = comments.length;
        
        // Build a nested tree from the flat comment list
        const commentTree = buildCommentTree(comments);
        
        // Clear old comments
        commentsListContainer.innerHTML = ''; 
        
        // Render the tree
        if (commentTree.length === 0) {
            commentsListContainer.innerHTML = '<p class="text-muted">No comments yet. Be the first to comment!</p>';
        } else {
            commentTree.forEach(comment => {
                commentsListContainer.innerHTML += createCommentHTML(comment);
            });
        }
      } catch (error) {
        console.error('Error fetching comments:', error);
        commentsListContainer.innerHTML = '<p class="text-danger">Could not load comments.</p>';
      }
    }

    /**
     * Posts a new comment or reply
     * @param {string} text - The comment content
     * @param {string|null} parentId - The ID of the parent comment (or null)
     */
    async function postComment(text, parentId = null) {
      try {
        const response = await fetch(`/api/jobs/${jobId}/comments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text,
            parent_id: parentId
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to post comment');
        }
        
        // Success! Clear the main textarea and re-fetch all comments
        commentTextarea.value = ''; 
        await fetchAndRenderComments(); // Refresh the list
        
      } catch (error) {
        console.error('Error posting comment:', error);
        alert('There was an error posting your comment.');
      }
    }

    /**
     * Converts a flat array of comments into a nested tree
     */
    function buildCommentTree(comments) {
      const commentMap = {};
      const tree = [];

      // 1. Create a map of all comments by their ID
      comments.forEach(comment => {
        commentMap[comment._id.$oid] = { ...comment, replies: [] };
      });

      // 2. Build the tree structure
      Object.values(commentMap).forEach(comment => {
        const parentId = comment.parent_id ? comment.parent_id.$oid : null;
        if (parentId && commentMap[parentId]) {
          // It's a reply, add it to its parent's replies array
          commentMap[parentId].replies.push(comment);
        } else {
          // It's a top-level comment
          tree.push(comment);
        }
      });
      
      return tree;
    }

    /**
     * Recursively creates the HTML for a comment and its replies
     */
    function createCommentHTML(comment) {
      const date = new Date(comment.timestamp.$date);
      const formattedDate = date.toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
      });
      
      // Generate HTML for all replies recursively
      let repliesHTML = '';
      if (comment.replies && comment.replies.length > 0) {
        repliesHTML = `
          <div class="mt-4">
            ${comment.replies.map(createCommentHTML).join('')}
          </div>
        `;
      }
      
      // Use a "data-" attribute to store the comment ID for replying
      return `
        <div class="d-flex mb-2 border border-dashed rounded p-3">
          <div class="flex-shrink-0">
            <img src="${comment.avatar_url || '{{ config.ASSETS_ROOT }}/images/users/user-placeholder.jpg'}" alt="${comment.username}" class="avatar-sm rounded-circle shadow-sm" />
          </div>
          <div class="flex-grow-1 ms-2">
            <h5 class="mb-1">
              ${comment.username}
              <small class="text-muted">${formattedDate}</small>
            </h5>
            <p class="mb-2">${comment.text}</p>
            <a href="javascript:void(0);" class="badge bg-light text-muted d-inline-flex align-items-center gap-1 reply-btn" data-comment-id="${comment._id.$oid}">
              <i class="ti ti-arrow-back-up fs-lg"></i>
              Reply
            </a>
            ${repliesHTML}
          </div>
        </div>
      `;
    }

    /**
     * Shows a temporary reply form under a parent comment
     */
    function showReplyForm(parentId, parentElement) {
      // Remove any existing reply forms
      const existingForm = document.getElementById('temp-reply-form');
      if (existingForm) {
        existingForm.remove();
      }
      
      // Create the new form
      const formHTML = `
        <form id="temp-reply-form" class="mt-3">
          <div class="mb-2">
            <textarea class="form-control" rows="3" placeholder="Write a reply..."></textarea>
          </div>
          <div class="text-end">
            <button type="button" class="btn btn-light btn-sm cancel-reply">Cancel</button>
            <button type="submit" class="btn btn-secondary btn-sm">Submit Reply</button>
          </div>
        </form>
      `;
      
      // Add the form after the parent comment's content
      parentElement.insertAdjacentHTML('beforeend', formHTML);
      
      const tempForm = document.getElementById('temp-reply-form');
      const tempTextarea = tempForm.querySelector('textarea');
      
      // Focus the new textarea
      tempTextarea.focus();
      
      // Handle submission
      tempForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const replyText = tempTextarea.value.trim();
        if (replyText) {
          await postComment(replyText, parentId);
          tempForm.remove(); // Clean up form on success
        }
      });
      
      // Handle cancel
      tempForm.querySelector('.cancel-reply').addEventListener('click', () => {
        tempForm.remove();
      });
    }

    // --- 3. EVENT LISTENERS ---

    // Handle top-level comment form submission
    commentForm.addEventListener('submit', async (e) => {
      e.preventDefault(); // Stop page reload
      const text = commentTextarea.value.trim();
      if (text) {
        await postComment(text, null); // null parentId for top-level
      }
    });

    // Handle "Reply" button clicks using event delegation
    commentsListContainer.addEventListener('click', (e) => {
      const replyButton = e.target.closest('.reply-btn');
      
      if (replyButton) {
        e.preventDefault();
        const parentId = replyButton.dataset.commentId;
        // Find the `flex-grow-1` div to append the form to
        const parentCommentBody = replyButton.closest('.flex-grow-1');
        showReplyForm(parentId, parentCommentBody);
      }
    });

    // --- 4. INITIAL LOAD ---
    fetchAndRenderComments();
    
  });
</script>