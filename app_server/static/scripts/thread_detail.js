const csrftoken = $('meta[name="csrf-token"]').attr("content");

$(".message-btn").click(function (e) {
    var threadId = $(this).attr("threadid");
    window.location.href = `/thread/${threadId}`;
  });