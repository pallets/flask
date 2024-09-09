document.addEventListener("DOMContentLoaded", function() {
    const toggleAllButton = document.getElementById("toggle-all");
    const postHeaders = document.querySelectorAll(".post-header");
    const posts = document.querySelectorAll(".post");

    toggleAllButton.addEventListener("click", function() {
        posts.forEach(post => {
            post.classList.toggle("collapsed");
        });
    });

    postHeaders.forEach(header => {
        header.addEventListener("click", function(event) {
            const postId = event.currentTarget.getAttribute("onclick").match(/\d+/)[0];
            togglePostBody(postId);
        });
    });
});

function togglePostBody(postId) {
    const postBody = document.getElementById(`post-body-${postId}`);
    const post = postBody.closest(".post");
    post.classList.toggle("collapsed");
}
