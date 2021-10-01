/**
*
* Google Image Layout v0.0.1
* Description, by Anh Trinh.
* Heavily modified for searx
* https://ptgamr.github.io/2014-09-12-google-image-layout/
* https://ptgamr.github.io/google-image-layout/src/google-image-layout.js
*
* @license Free to use under the MIT License.
*
*/

(function (w, d) {
  function ImageLayout(container_selector, results_selector, img_selector, margin, maxHeight) {
    this.container_selector = container_selector;
    this.results_selector = results_selector;
    this.img_selector = img_selector;
    this.margin = margin;
    this.maxHeight = maxHeight;
    this.isAlignDone = true;
  }

  /**
  * Get the height that make all images fit the container
  *
  * width = w1 + w2 + w3 + ... = r1*h + r2*h + r3*h + ...
  *
  * @param  {[type]} images the images to be calculated
  * @param  {[type]} width  the container witdth
  * @param  {[type]} margin the margin between each image
  *
  * @return {[type]}        the height
  */
  ImageLayout.prototype._getHeigth = function (images, width) {
    var i, img;
    var r = 0;

    for (i = 0; i < images.length; i++) {
      img = images[i];
      if ((img.naturalWidth > 0) && (img.naturalHeight > 0)) {
        r += img.naturalWidth / img.naturalHeight;
      } else {
        // assume that not loaded images are square
        r += 1;
      }
    }

    return (width - images.length * this.margin) / r; //have to round down because Firefox will automatically roundup value with number of decimals > 3
  };

  ImageLayout.prototype._setSize = function (images, height) {
    var i, img, imgWidth;
    var imagesLength = images.length, resultNode;

    for (i = 0; i < imagesLength; i++) {
      img = images[i];
      if ((img.naturalWidth > 0) && (img.naturalHeight > 0)) {
        imgWidth = height * img.naturalWidth / img.naturalHeight;
      } else {
        // not loaded image : make it square as _getHeigth said it
        imgWidth = height;
      }
      img.style.width = imgWidth + 'px';
      img.style.height = height + 'px';
      img.style.marginLeft = '3px';
      img.style.marginTop = '3px';
      img.style.marginRight = this.margin - 7 + 'px'; // -4 is the negative margin of the inline element
      img.style.marginBottom = this.margin - 7 + 'px';
      resultNode = img.parentNode.parentNode;
      if (!resultNode.classList.contains('js')) {
        resultNode.classList.add('js');
      }
    }
  };

  ImageLayout.prototype._alignImgs = function (imgGroup) {
    var isSearching, slice, i, h;
    var containerElement = d.querySelector(this.container_selector);
    var containerCompStyles = window.getComputedStyle(containerElement);
    var containerPaddingLeft = parseInt(containerCompStyles.getPropertyValue('padding-left'), 10);
    var containerPaddingRight = parseInt(containerCompStyles.getPropertyValue('padding-right'), 10);
    var containerWidth = containerElement.clientWidth - containerPaddingLeft - containerPaddingRight;

    while (imgGroup.length > 0) {
      isSearching = true;
      for (i = 1; i <= imgGroup.length && isSearching; i++) {
        slice = imgGroup.slice(0, i);
        h = this._getHeigth(slice, containerWidth);
        if (h < this.maxHeight) {
          this._setSize(slice, h);
          // continue with the remaining images
          imgGroup = imgGroup.slice(i);
          isSearching = false;
        }
      }
      if (isSearching) {
        this._setSize(slice, Math.min(this.maxHeight, h));
        break;
      }
    }
  };

  ImageLayout.prototype.align = function () {
    var i;
    var results_selectorNode = d.querySelectorAll(this.results_selector);
    var results_length = results_selectorNode.length;
    var previous = null;
    var current = null;
    var imgGroup = [];

    for (i = 0; i < results_length; i++) {
      current = results_selectorNode[i];
      if (current.previousElementSibling !== previous && imgGroup.length > 0) {
        // the current image is not connected to previous one
        // so the current image is the start of a new group of images.
        // so call _alignImgs to align the current group
        this._alignImgs(imgGroup);
        // and start a new empty group of images
        imgGroup = [];
      }
      // add the current image to the group (only the img tag)
      imgGroup.push(current.querySelector(this.img_selector));
      // update the previous variable
      previous = current;
    }
    // align the remaining images
    if (imgGroup.length > 0) {
      this._alignImgs(imgGroup);
    }
  };

  ImageLayout.prototype.watch = function () {
    var i, img;
    var obj = this;
    var results_nodes = d.querySelectorAll(this.results_selector);
    var results_length = results_nodes.length;

    function throttleAlign() {
      if (obj.isAlignDone) {
        obj.isAlignDone = false;
        setTimeout(function () {
          obj.align();
          obj.isAlignDone = true;
        }, 100);
      }
    }

    w.addEventListener('pageshow', throttleAlign);
    w.addEventListener('load', throttleAlign);
    w.addEventListener('resize', throttleAlign);

    for (i = 0; i < results_length; i++) {
      img = results_nodes[i].querySelector(this.img_selector);
      if (img !== null && img !== undefined) {
        img.addEventListener('load', throttleAlign);
        img.addEventListener('error', throttleAlign);
      }
    }
  };

  w.searxng.ImageLayout = ImageLayout;

}(window, document));
