/** Class UploadClient. this class is used for uploading files to the server and processing them. */
class UploadClient {
  /**
   * Create Upload Client instance.
   *
   * @param {string} client_id - oauth client_id
   */
  constructor(client_id) {
    this.queue = []
    this.client_id = client_id
    this.client_uuid = ""
    this.oauth = new OauthClient(client_id);
    this.finished = [];
    const cookie = this.getCookie("uc_uuid");
    if (cookie) {
      this.client_uuid = cookie;
    } else {
      this.client_uuid = this.generateUUID();
      this.setCookie("uc_uuid", this.client_uuid, 1);
    }
  }

  //Add uploaded file to process queue
  addToQueue(uuid, file) {
    this.queue.push({uuid: uuid, file: file, tasks: []});
  }

  /**
   * Resize the picture keeping the AR
   *
   * @param {object} file - File 
   * @param {number} width - Width 
   * @param {number} height - Height 
   * @param {string} mimetype - MimeType
   * @returns {Promise<Token>} 
   */
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

  /**
   * Crop the picture to requested AR 
   *
   * @param {object} file - File 
   * @param {number} width - Width 
   * @param {number} height - Height 
   * @param {string} mimetype - MimeType
   * @returns {Promise<Token>} 
   */
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

  /**
   * Exstract Exif information from image 
   *
   * @param {object} file - File 
   * @returns {Promise<Token>} 
   */
  async exif(file) {
    return window.exifr.parse(file.dataURL)
  }

  /**
   * Process a job item from the queue 
   *
   * @param {object} item - Item to process 
   * @param {object} job - Job information 
   * @returns {Promise<Token>} 
   */
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
        return this.uploadJobResult(job, JSON.stringify(exif))
    }
  }

  /**
   * Fetch the joblist from server 
   *
   * @param {object} item - Item to process 
   * @returns {Promise<Token>} 
   */
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

  /**
   * Upload the job results to the server 
   *
   * @param {object} item - Item to process 
   * @returns {array} bma_response 
   */
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

  /**
   * Create a album from the items in the finished arrach 
   *
   * @param {string} name - Name of the album.
   * @param {string} description - Description of the album.
   * @returns {array} bma_response 
   */
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


  /**
   * Process the next item in the queue 
   *
   */
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

  /**
   * Update the dropzone item progress bar 
   *
   * @param {object} item - Item 
   * @param {number} progress - Progress percentage.
   * @returns {array} bma_response 
   */
  updateProgress(item, progress) {
    for (let node of item.file.previewElement.querySelectorAll(
      "[data-dz-uploadprogress]"
    )) {
      node.nodeName === "PROGRESS"
        ? (node.value = progress)
        : (node.style.width = `${progress}%`);
    }
  }

  /**
   * Set a cookie 
   *
   * @param {string} cname - Name of the cookie 
   * @param {string} cvalue - Value of the cookie. 
   * @param {number} exdays - Days of validity.
   * @returns {string} Cookie contents 
   */
  setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
  }

  /**
   * Get a cookie 
   *
   * @param {string} cname - Name of the cookie 
   * @returns {string} Cookie contents 
   */
  getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }

  /**
   * Generate UUID 
   *
   * @returns {string} UUID 
   */
  generateUUID() { // Public Domain/MIT
    var d = new Date().getTime();//Timestamp
    var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now()*1000)) || 0;//Time in microseconds since page-load or 0 if unsupported
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16;//random number between 0 and 16
      if(d > 0){//Use timestamp until depleted
        r = (d + r)%16 | 0;
        d = Math.floor(d/16);
      } else {//Use microseconds since page-load if supported
        r = (d2 + r)%16 | 0;
        d2 = Math.floor(d2/16);
      }
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
}
