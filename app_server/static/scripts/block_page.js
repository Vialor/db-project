const csrftoken = $('meta[name="csrf-token"]').attr("content");

$(".follow-btn").click(function (e) {
  var blockId = $(this).attr("blockid");
  fetch(`block/follow/${blockId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({}),
  });
  console.log("Follow button clicked for block id: " + blockId);
});

$(".join-btn").click(function (e) {
  var blockId = $(this).attr("blockid");
  fetch(`block/apply/${blockId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({}),
  });
  console.log("Join button clicked for block id: " + blockId);
});
