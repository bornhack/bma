/** Class UploadClient. this class is used for uploading files to the server and processing them. */
class UploadClient {
  /**
   * Create Upload Client instance.
   *
   * @param {string} client_id - oauth client_id
   * @param {function} callback - Done loading callback 
   */
  constructor(client_id, callback) {
    this.run = true;
    this.log = (log) => { console.log(log) } 
    this.queue = []
    this.client_id = client_id
    this.client_uuid = ""
    this.oauth = new OauthClient(client_id, (token) => this.oauthReady(token));
    this.finished = [];
    this.allowedMimetypes = [];
    this.callback = callback;
    this.bma_version = JSON.parse(document.getElementById('bma_version').textContent);
    this.client_version = `js-client - BMA ${this.bma_version}`;
    this.activeJobs = 0;
    this.maxConcurrent = 2;
    const cookie = this.getCookie("uc_uuid");
    if (cookie) {
      this.client_uuid = cookie;
    } else {
      this.client_uuid = this.generateUUID();
      this.setCookie("uc_uuid", this.client_uuid, 1);
    }
    this.updateProgress = (_item, _progress) => {};
  }

  /**
   * OAuth token callback
   *
   * @param {string} token - OAuth token
   */
  oauthReady(_token) {
    this.getClientConfig();
  }

  /**
   * Add uploaded file to process queue 
   *
   * @param {string} uuid - UUID of the uploaded file 
   * @param {object} file - File object
   */
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
        convertSize: -1,
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
    if ("dataURL" in file)
      return window.exifr.parse(file.dataURL)
    else
      console.log("Exif missing dataURL");
  }

  /**
   * Reformat exif data to schema used in BMA 
   *
   * @param {object} originalData - Original exif. 
   * @returns {object} Reformatted exif data. 
   */
  reformatExifData(originalData) {
    const formattedData = {
      Image: {},
      Thumbnail: {},
      EXIF: {},
    };

    // Map of property name changes if any
    const propertyMap = {
      "ISO": "ISOSpeedRatings",
      "ExposureCompensation": "ExposureBiasValue",
    };

    for (const key in originalData) {
      const value = originalData[key];
      const newKey = propertyMap[key] || key;

      if (typeof newKey === 'object') {
        newKey = newKey[value];
      }

      if (['ImageWidth', 'ImageHeight', 'Make', 'Model', 'Orientation', 'XResolution', 'YResolution', 'ResolutionUnit', 'Software', 'DateTime', 'YCbCrPositioning', 'ExifOffset'].includes(newKey)) {
        formattedData.Image[newKey] = value.toString();
      } else if ([].includes(newKey)) {
        formattedData.Thumbnail[newKey] = value.toString();
      } else {
        formattedData.EXIF[newKey] = value.toString();
      }
    }
    return formattedData;
  }

  /**
   * Process a job item from the queue 
   *
   * @param {object} item - Item to process 
   * @param {object} job - Job information 
   * @returns {Promise} - The promise 
   */
  async processJob(item, job) {
    switch(job.job_type) {
      case "ImageConversionJob":
        const filename = `${job.job_uuid}.${job.filetype}`
        this.log(`Job for ${job.basefile_uuid}: ${job.job_type} ${job.width}x${job.height} ${job.mimetype} Custom aspect ratio: ${job.custom_aspect_ratio}`)
        if (job.custom_aspect_ratio)
          return this.crop(item.file, job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img, filename)
          });
        else
          return this.resize(item.file, job.width, job.height, job.mimetype).then(img=> {
            this.uploadJobResult(job, img, filename)
          });
      /*
      case "ImageExifExtractionJob":
        this.log(`Job for ${job.basefile_uuid}: ${job.job_type} ${job.job_uuid}`)
        const exifOrg = await this.exif(item.file);
        const exif = this.reformatExifData(exifOrg);
        const jsonFile = new Blob([JSON.stringify(exif)], { type: 'application/json' });
        console.log(exifOrg, exif);
        return this.uploadJobResult(job, jsonFile, "exif.json");
      */
      default:
        this.log(`Unsupported job type: ${job.job_type} ${job.job_uuid}`);
        break; 
    }
  }

  /**
   * Fetch file meta data from server 
   *
   * @param {object} job - Job entry 
   * @returns {Promise<Token>} 
   */
  async fetchFileMetadata(job) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/files/${job.basefile_uuid}/`);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch file
   *
   * @param {string} url - URL of the file to fetch 
   * @returns {Promise<Token>} 
   */
  async fetchFile(file_url) {
    try {
      const url = new URL(file_url)
      const result = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      return await result.blob()
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch the file list from server 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise<Token>} 
   */
  async fetchFileList(query) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/files/`);
      url.search = new URLSearchParams(query);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Fetch the joblist from server 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise<Token>} 
   */
  async fetchJobList(query) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/jobs/`);
      url.search = new URLSearchParams(query);
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Assign the job to this client 
   *
   * @param {object} query - Query to execute 
   * @returns {Promise<Token>} 
   */
  async assignJob(uuid) {
    try {
      const url = new URL(`${window.location.origin}/api/v1/json/jobs/assign/`);
      url.search = new URLSearchParams({finished: false, file_uuid: uuid});
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
          "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify({ "client_uuid": this.client_uuid, "client_version": this.client_version }),
      });
      console.log(response)
      if (!response.ok) {
        this.log(`Failed to assign jobs for ${uuid}`);
        throw new Error(`Response status: ${response.status}`);
      }

      const json = await response.json();
      return json.bma_response 
    } catch (error) {
      console.log(error.message);
      return [];
    }
  }

  /**
   * Upload the job results to the server 
   *
   * @param {object} item - Item to process 
   * @param {object} result - Result to upload. 
   * @param {string} filename - Name of the file 
   * @returns {array} bma_response 
   */
  async uploadJobResult(job, result, filename) {
    var data = new FormData()
    data.append('f', result, filename);
    data.append('client', JSON.stringify({ "client_uuid": this.client_uuid, "client_version": this.client_version }))

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
      console.log(error.message);
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
      console.log(error.message);
      return [];
    }
  }


  /**
   * Process the next item in the queue 
   *
   */
  async processNext() {
    if (this.queue.length === 0 || this.activeJobs >= this.maxConcurrent || this.run === false) {
      return;
    }
    const item = this.queue.shift();
    try {
      let jobsDone = 0;
      this.activeJobs++;

      // Fetch job list from API
      const jobList = await this.assignJob(item.uuid);
      this.finished.push(item.uuid);

      //Set progress bar to 0%
      this.updateProgress(item, 0);

      // Process each job
      for (const job of jobList) {
        if (!job.finished && this.run) {
          await this.processJob(item, job);
        }
        jobsDone++;
        this.updateProgress(item, (jobsDone * 100) / jobList.length);
      }
      //Produce some user feedback
      if ("previewElement" in item.file) {
        item.file.previewElement.classList.add("dz-complete");
        item.file.previewElement.classList.add("dz-success");
      }
    } catch (error) {
      this.activeJobs--;
      this.processNext(); // Process the next item in the queue
      this.updateProgress(item, 100);
      console.log(`Error processing Item ${item.uuid}:`, error);
    } finally {
      this.activeJobs--;
      this.processNext(); // Process the next item in the queue
      this.updateProgress(item, 100);
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

  /**
   * Extract keys from object 
   *
   * @param {object} obj - Object
   * @returns {array} Keys
   */
  extractKeys(obj) {
    const keys = [];
    for (const key in obj) {
      if (typeof obj[key] === 'object') {
        keys.push(...this.extractKeys(obj[key]));
      } else {
        keys.push(key);
      }
    }
    return keys;
  }

  /**
   * Get client configuration from server.
   *
   */
  async getClientConfig() {
    try {
      const response = await fetch(`/api/v1/json/jobs/settings/`, {
        headers: {
          "Authorization": `Bearer ${this.oauth.token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
      }
      this.finished = [];
      const json = await response.json();
      this.config = json.bma_response;
      this.allowedMimetypes = this.extractKeys(this.config.filetypes)
      this.callback();
    } catch (error) {
      console.log(error.message);
    }
  }

}
