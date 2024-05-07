const csrftoken = $('meta[name="csrf-token"]').attr("content");

$(".message-btn").click(function (e) {
    var threadId = $(this).attr("threadid");
    fetch(`thread/${threadId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({}),
    });
    console.log("Follow button clicked for thread id: " + threadId);
  });