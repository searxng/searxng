const qinput = document.getElementById('q');

function submitIfQuery() {
  if (qinput.value.length > 0) {
    var search = document.getElementById('search');
    setTimeout(search.submit.bind(search), 0);
  }
}

// vanilla js version of search_on_category_select.js
if (qinput !== null && document.querySelector('.help') != null) {
  document.querySelector('.help').className = 'invisible';

  searxng.on('#categories input', 'change', function () {
    var i, categories = document.querySelectorAll('#categories input[type="checkbox"]');
    for (i = 0; i < categories.length; i++) {
      if (categories[i] !== this && categories[i].checked) {
        categories[i].click();
      }
    }
    if (!this.checked) {
      this.click();
    }
    submitIfQuery();
    return false;
  });

  searxng.on(document.getElementById('safesearch'), 'change', submitIfQuery);
  searxng.on(document.getElementById('time_range'), 'change', submitIfQuery);
  searxng.on(document.getElementById('language'), 'change', submitIfQuery);
}
