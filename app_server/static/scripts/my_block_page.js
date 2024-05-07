const csrftoken = $('meta[name="csrf-token"]').attr("content");

$(".approve-btn").click(function (e) {
  var applicationId = $(this).attr("applicationid");
  fetch(`approve-application/${applicationId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({}),
  });
  console.log("Approve button clicked for application id: " + applicationId);
});
