const client_id = JSON.parse(document.getElementById('client_id').textContent);

const UC = new UploadClient(client_id, () => {
  $('#btnstart').html("Start Grinding");
  $('#btnstart').removeAttr('disabled');
  UC.log("Loaded UC client");
});

UC.onFinished = (active) => {
  if (active === 0) {
    UC.log("Fetching new work");
    UC.assignJob().then((jobs)=>{
      if (!jobs)
        return
      if (jobs.length > 0)
        UC.fetchNewWork();
      else {
        UC.log("Finished");
        if (UC.running_jobs === 0) {
          $('#btnstop').attr("disabled", "true");
          $('#btnstart').removeAttr("disabled");
        }
      }
    })
  }
}

UC.onDeQueue = (active, jobs, current, total, _element) => {
  console.log(`Active jobs: ${active} left in Queue: ${jobs} Current: ${current} Total: ${total}`)
  if (jobs > 0) {
    const pct = ((current - jobs + 1)/current*100);
    document.getElementsByClassName('progress-bar').item(0).setAttribute('aria-valuenow', pct);
    document.getElementsByClassName('progress-bar').item(0).setAttribute('style','width:'+Number(pct)+'%');
  }
}

UC.log = (log) => {
  console.log(log);
  var node = document.createElement("li");
  node.classList.add("list-group-item");
  node.appendChild(document.createTextNode(log));
  document.getElementById("job_log").prepend(node);
}

jQuery(document).ready(() => {
  $("#btnstart").bind("click", () => {
    $('#btnstart').attr("disabled", "true");
    $('#btnstop').removeAttr("disabled");
    if (UC.run) {
      UC.fetchNewWork();
    }
    else
      UC.startGrinder();
  })
  $("#btnstop").bind("click", () => {
    UC.run = false;
    $('#btnstop').attr("disabled", "true");
    $('#btnstart').removeAttr("disabled");
  })
});
