const client_id = JSON.parse(document.getElementById('client_id').textContent);
var myFiles = [];
var done = {};
var jobCount = 0;
var jobCountTotal = 0;
var filesFetched = {};

function fetchWork(callback = ()=>{}) {
  const query = {
    jobs: true,
    limit: 2,
  };
  myFiles = [];
  jobCountTotal = 0;
  jobCount = 0;
  return UC.fetchFileList(query).then(files => {
    myFiles = files;
    let fileCounted = {}
    for (const file of myFiles) {
      if (!(file.uuid in fileCounted)) {
        fileCounted[file.uuid] = true;
        jobCount = jobCount + file.jobs_unfinished.length;
      }
    }
    $('#job_count').html(`Grinding ${jobCount} jobs`);
    jobCountTotal = jobCount;
    jobCount = 0;
    if (jobCountTotal > 0)
      $('#btnstart').removeAttr("disabled");
    callback(files);
  });
}

function runJobs() {
  UC.run = true;
  $('#btnstart').attr("disabled", "true");
  $('#btnstop').removeAttr("disabled");
  for (const sourceFile of myFiles) {
    if (!(sourceFile.uuid in filesFetched)) {
      filesFetched[sourceFile.uuid] = true;
      UC.log(`Fetching file ${sourceFile.uuid}`)
      UC.fetchFile(`${window.location.origin}${sourceFile.links.downloads.original}`).then( (img) => {
        if (img.type.startsWith("image/") && img.size > 0) {
          const file = new File([img], sourceFile.filename, {
            lastModified: new Date(),
            type: img.type,
          });
          console.log(file, img);
          UC.addToQueue(sourceFile.uuid, file); 
          UC.processNext();
        }
      }).catch(() => {
        UC.processNext();
      })
    }
    UC.processNext();
  }
}

const UC = new UploadClient(client_id, () => {
  $('#btnstart').html("Start Grinding");
  UC.log("Loaded UC client");
  fetchWork();
});

UC.updateProgress = (_item, _percent) => {
  if (jobCount >= jobCountTotal && UC.run) {
    console.log("Fetch new work")
    fetchWork((_files) => {
      runJobs();
    });
  } 
  if (UC.run === false) {
    $('#btnstop').attr("disabled", "true");
    $('#btnstart').removeAttr("disabled");
  }
  jobCount++;
  const pct = (jobCount/jobCountTotal*100);
  document.getElementsByClassName('progress-bar').item(0).setAttribute('aria-valuenow', pct);
  document.getElementsByClassName('progress-bar').item(0).setAttribute('style','width:'+Number(pct)+'%');
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
    runJobs();
  })
  $("#btnstop").bind("click", () => {
    UC.run = false;
  })
});
