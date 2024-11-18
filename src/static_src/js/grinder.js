const client_id = JSON.parse(document.getElementById('client_id').textContent);
var myFiles = [];
var done = {};
var jobCount = 0;
var jobCountTotal = 0;
var filesFetched = {};

/*
 * Step 1: Fetch unprocessed jobs for this client.
 * Step 1a: Fetch sources for these jobs.
 * Step 2: Process jobs from step 1
 * Step 3: Fetch new jobs from assign
 * Step 3a: Fetch sources for these jobs.
 * Step 4: Process jobs from step 3
 * Step 5: Cleanup memory
 * Step 6: Goto 1 with all skipped jobs to query
 */

function step1() {
  let downloadJobs = [];
  UC.fetchJobList({client_uuid: UC.client_uuid, finished: false}).then((jobs) => {
    for (const file of UC.getUnique(jobs, "source_url")) {
      if (!(file in UC.source_file_store))
        downloadJobs.push(UC.fetchFile(file));
    }
    Promise.all(downloadJobs).then((imgs)=> {
      for (const img of imgs) {
        UC.storeSource(img.url, img.file);
      }
      for (const job of jobs) {
        UC.addToJobQueue(job.basefile_uuid, job);
      }
      UC.startGrinder();
    })
  });
}

function step3() {
  UC.log("Fetching new work");
  UC.assignJob().then((jobs)=>{
    if (!jobs)
      return
    if (jobs.length > 0)
      step1();
    else {
      console.log("Finished");
      if (UC.running_jobs === 0) {
        $('#btnstop').attr("disabled", "true");
        $('#btnstart').removeAttr("disabled");
      }
    }
  })
}

const UC = new UploadClient(client_id, () => {
  $('#btnstart').html("Start Grinding");
  $('#btnstart').removeAttr('disabled');
  UC.log("Loaded UC client");
});

UC.onFinished = (active) => {
  if (active === 0)
    step3();
}

UC.onDeQueue = (active, jobs, current, total, _element) => {
  UC.log(`Active jobs: ${active} left in Queue: ${jobs} Current: ${current} Total: ${total}`)
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
    if (UC.run)
      step1();
    else
      UC.startGrinder();
  })
  $("#btnstop").bind("click", () => {
    UC.run = false;
    $('#btnstop').attr("disabled", "true");
    $('#btnstart').removeAttr("disabled");
  })
});
