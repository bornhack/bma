class UploadClient {
  constructor() {
    this.queue = []
  }

  //Add uploaded file to process queue
  addToQueue(uuid, file) {
    this.queue.push({uuid: uuid, file: file, tasks: []});
  }

  //Resize file returns Blob
  async resize(file, size, type = ['image/png']) {
    return new Promise((resolve, reject) => {
      new Compressor(file, {
        quality: 0.6,  
        maxWidth: size, 
        convertTypes: type,
        success(result) {
          resolve(result);
        },             
        error(err) {                
          console.log(err.message);
          reject(err);
        },                          
      });
    });
  }

  //Returns Promis
  async exif(file) {
    return window.exifr.parse(file.dataURL)
  }

  async process(item, job) {
    switch(job.type) {
      case "resize":
        this.resize(item.file, job.width).then(img=> {
          document.getElementById('preview').src = window.URL.createObjectURL(img);
        });
        break;
      case "exif":
        const exif = await this.exif(item.file, job.width);
        console.log(exif)
        break;
    }
  }

  updateProgress(item, progress) {
    for (let node of item.file.previewElement.querySelectorAll(
      "[data-dz-uploadprogress]"
    )) {
      node.nodeName === "PROGRESS"
        ? (node.value = progress)
        : (node.style.width = `${progress}%`);
    }
  }

  async fetchJobList(item) {
    // Fetch jobs /api/v1/json/jobs/assign/?file_uuid=
    // Simulate fetching job list from API
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`Fetching /api/v1/json/jobs/assign/?file_uuid=${item.uuid}`)
        resolve([
          { id: 1, name: "Job resize 500", type: 'resize', width: 500 },
          { id: 2, name: "Job resize 100", type: 'resize', width: 100 },
          { id: 3, name: "Job resize 200", type: 'resize', width: 200 },
          { id: 4, name: "Job resize 300", type: 'resize', width: 300 },
          { id: 5, name: "Job read exif", type: 'exif' },
        ]);
      }, 1000);
    });
    /*
    try {
      const response = await fetch(`/api/v1/json/jobs/assign/?file_uuid=${item.uuid}`);
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      const json = await response.json();
      return json 
    } catch (error) {
      console.error(error.message);
      return [];
    }
    */
  }

  async processJob(item, job) {
    // Simulate job processing
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`Processing job: ${job.name} for ${item.uuid}`);
        this.process(item, job);
        resolve();
      }, 500);
    });
  }

  async processNext() {
    if (this.queue.length === 0) {
      return;
    }

    const item = this.queue.shift();
    try {
      // Fetch job list from API
      const jobList = await this.fetchJobList(item);

      //Set progress bar to 0%
      this.updateProgress(item, 0);

      // Process each job
      let jobsDone = 0;
      for (const job of jobList) {
        await this.processJob(item, job);
        jobsDone++;
        this.updateProgress(item, (jobsDone * 100) / jobList.length); 
      }
      //Produce some user feedback
      item.file.previewElement.classList.add("dz-complete");
      item.file.previewElement.classList.add("dz-success");
    } catch (error) {
      console.error(`Error processing Item ${item.uuid}:`, error);
    } finally {
      this.processNext(); // Process the next item in the queue
    }
  }
}
