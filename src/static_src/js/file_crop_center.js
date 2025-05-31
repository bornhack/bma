$(document).ready(function(){
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  var xhr = new XMLHttpRequest();

  function update_size() {
    canvas.height = Number(document.getElementById("ratio-selector").value)
    canvasHeight=canvas.height;
    draw();
  }

  function draw() {
    if (!xhr.response) return;
    const width = canvas.width;
    const height = canvas.height;
      new Compressor(xhr.response, {
        quality: 0.6,
        width: width,
        height: height,
        resizeCenterX: document.getElementById("id_center_x").value,
        resizeCenterY: document.getElementById("id_center_y").value,
        mimeType: "image/png",
        convertSize: -1,
        resize: 'crop',
        success(result) {
          var newImage = new Image();
          newImage.src = URL.createObjectURL(result);
          newImage.alt = 'Compressed image';
          newImage.onload = () => {
            ctx.drawImage(newImage, 0, 0); 
          }
        },
        error(err) {
          console.log(err.message);
        },
      });
  }
  xhr.onload = function () {
    draw();
  }

  xhr.open('GET', JSON.parse(document.getElementById('file').textContent));
  xhr.responseType = 'blob';
  xhr.send();

  document.getElementById("id_center_x").addEventListener('change', draw);
  document.getElementById("id_center_y").addEventListener('change', draw);
  document.getElementById("ratio-selector").addEventListener('change', update_size);
} );
