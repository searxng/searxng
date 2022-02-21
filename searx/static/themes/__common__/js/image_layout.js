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
* @example <caption>Example usage of searxng.ImageLayout class.</caption>
* searxng.image_thumbnail_layout = new searxng.ImageLayout(
*     '#urls',                 // container_selector
*     '#urls .result-images',  // results_selector
*     'img.image_thumbnail',   // img_selector
*     14,                      // verticalMargin
*     6,                       // horizontalMargin
*     200                      // maxHeight
* );
* searxng.image_thumbnail_layout.watch();
*/


(function (w, d) {
  function ImageLayout (container_selector, results_selector, img_selector, verticalMargin, horizontalMargin, maxHeight) {
    this.container_selector = container_selector;
    this.results_selector = results_selector;
    this.img_selector = img_selector;
    this.verticalMargin = verticalMargin;
    this.horizontalMargin = horizontalMargin;
    this.maxHeight = maxHeight;
    this.trottleCallToAlign = null;
    this.alignAfterThrotteling = false;
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

    return (width - images.length * this.verticalMargin) / r; // have to round down because Firefox will automatically roundup value with number of decimals > 3
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
      img.setAttribute('width', Math.round(imgWidth));
      img.setAttribute('height', Math.round(height));
      img.style.marginLeft = Math.round(this.horizontalMargin) + 'px';
      img.style.marginTop = Math.round(this.horizontalMargin) + 'px';
      img.style.marginRight = Math.round(this.verticalMargin - 7) + 'px'; // -4 is the negative margin of the inline element
      img.style.marginBottom = Math.round(this.verticalMargin - 7) + 'px';
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

  ImageLayout.prototype.throttleAlign = function () {
    var obj = this;
    if (obj.trottleCallToAlign) {
      obj.alignAfterThrotteling = true;
    } else {
      obj.alignAfterThrotteling = false;
      obj.align();
      obj.trottleCallToAlign = setTimeout(function () {
        if (obj.alignAfterThrotteling) {
          obj.align();
        }
        obj.alignAfterThrotteling = false;
        obj.trottleCallToAlign = null;
      }, 20);
    }
  }

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

  ImageLayout.prototype._monitorImages = function () {
    var i, img;
    var objthrottleAlign = this.throttleAlign.bind(this);
    var results_nodes = d.querySelectorAll(this.results_selector);
    var results_length = results_nodes.length;

    function img_load_error (event) {
      // console.log("ERROR can't load: " + event.originalTarget.src);
      event.originalTarget.src = w.searxng.static_path + w.searxng.theme.img_load_error;
    }

    for (i = 0; i < results_length; i++) {
      img = results_nodes[i].querySelector(this.img_selector);
      if (img !== null && img !== undefined && !img.classList.contains('aligned')) {
        img.addEventListener('load', objthrottleAlign);
        // https://developer.mozilla.org/en-US/docs/Web/API/GlobalEventHandlers/onerror
        img.addEventListener('error', objthrottleAlign);
        img.addEventListener('timeout', objthrottleAlign);
        if (w.searxng.theme.img_load_error) {
          img.addEventListener('error', img_load_error, {once: true});
        }
        img.classList.add('aligned');
      }
    }
  }

  ImageLayout.prototype.watch = function () {
    var objthrottleAlign = this.throttleAlign.bind(this);

    // https://developer.mozilla.org/en-US/docs/Web/API/Window/pageshow_event
    w.addEventListener('pageshow', objthrottleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/FileReader/load_event
    w.addEventListener('load', objthrottleAlign);
    // https://developer.mozilla.org/en-US/docs/Web/API/Window/resize_event
    w.addEventListener('resize', objthrottleAlign);

    this._monitorImages();

    var obj = this;

    let observer = new MutationObserver(entries => {
      let newElement = false;
      for (let i = 0; i < entries.length; i++) {
        if (entries[i].addedNodes.length > 0 && entries[i].addedNodes[0].classList.contains('result')) {
          newElement = true;
          break;
        }
      }
      if (newElement) {
        obj._monitorImages();
      }
    });
    observer.observe(d.querySelector(this.container_selector), {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: false,
    })
  };

  w.searxng.ImageLayout = ImageLayout;

}(window, document));
