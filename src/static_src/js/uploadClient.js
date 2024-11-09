class UploadClient {
  constructor(client_id) {
    this.queue = []
    this.client_id = client_id
    this.client_uuid = "12345678-1234-1234-1234-deadbeaf4242"
    this.oauth = new OauthClient(client_id);
    this.finished = [];
  }

  //Add uploaded file to process queue
  addToQueue(uuid, file) {
    this.queue.push({uuid: uuid, file: file, tasks: []});
  }

  //Resize file returns Blob
  async resize(file, width, height, type = 'image/png') {
    return new Promise((resolve, reject) => {
      new Compressor(file, {
        quality: 0.6,  
        maxWidth: width,
        maxHeight: height,
        mimeType: type,
        convertSize: 50000000,
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

  async crop(file, width, height, type = 'image/png') {
    return new Promise((resolve, reject) => {
      new Compressor(file, {
        quality: 0.6,  
        width: width,
        height: height,
        mimeType: type,
        convertSize: 50000000,
        resize: 'cover',
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

  async processJob(item, job) {
    switch(job.job_type) {
      case "ImageConversionJob":
        console.log(`Job for ${job.basefile_uuid}: ${job.job_type} ${job.width}x${job.height} ${job.mimetype} Custom aspect ratio: ${job.custom_aspect_ratio}`)
        if (job.custom_aspect_ratio)
          return this.crop(item.file, job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img)
          });
        else
          return this.resize(item.file, job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img)
          });
      case "ImageExifExtractionJob":
        console.log(`Job for ${job.basefile_uuid}: ${job.job_type}`)
        const exif = await this.exif(item.file);
        console.log(exif)
        return this.uploadJobResult(job, JSON.stringify(exif))
    }
  }

  async fetchJobList(item) {
    // Fetch jobs /api/v1/json/jobs/assign/?file_uuid=
    try {
      const response = await fetch(`/api/v1/json/jobs/assign/?finished=false&file_uuid=${item.uuid}`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({ "client_uuid": this.client_uuid }),
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      this.finished.push(item.uuid);

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.error(error.message);
      return [];
    }
  }

  async uploadJobResult(job, file) {
    // Fetch jobs /api/v1/json/jobs/assign/?file_uuid=
    var data = new FormData()
    data.append('f', file)
    data.append('assign', JSON.stringify({ "client_uuid": this.client_uuid }))

    try {
      const response = await fetch(`/api/v1/json/jobs/${job.job_uuid}/result/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
        method: "POST",
        body: data,
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.error(error.message);
      return [];
    }
  }

  async createAlbum(name, description) {
    var data = {
      'title': name,
      'description': description,
      'files': this.finished,
    }
    if (this.finished.length === 0) return
    try {
      const response = await fetch(`/api/v1/json/albums/create/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      this.finished = [];
      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.error(error.message);
      return [];
    }
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
        if (!job.finished) {
          await this.processJob(item, job);
        }
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

  //Update dropzone status bar
  updateProgress(item, progress) {
    for (let node of item.file.previewElement.querySelectorAll(
      "[data-dz-uploadprogress]"
    )) {
      node.nodeName === "PROGRESS"
        ? (node.value = progress)
        : (node.style.width = `${progress}%`);
    }
  }
}
