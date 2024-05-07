const csrftoken = $('meta[name="csrf-token"]').attr("content");

$(document).ready(function () {
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
});

// fetch(`/user/events/${event_id}/remove-interest/`, {
//   method: "POST",
//   headers: {
//     "Content-Type": "application/json",
//     "X-CSRFToken": csrftoken,
//   },
//   body: JSON.stringify({}),
// })
//   .then((response) => response.json())
//   .then((data) => {
//     location.reload(true);
//   })
//   .catch((error) => {
//     console.error("Error:", error);
//   });
