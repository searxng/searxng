/*
When showing the sticky version warning, the warning will cover the
scroll target when navigating to #id hash locations. Take over scrolling
to adjust the position to account for the height of the warning.
*/
$(() => {
  const versionWarning = $('.version-warning')

  // Skip if there is no version warning, regular browser behavior is
  // fine in that case.
  if (versionWarning.length) {
    const height = versionWarning.outerHeight(true)
    const target = $(':target')

    // Adjust position when the initial link has a hash.
    if (target.length) {
      // Use absolute scrollTo instead of relative scrollBy to avoid
      // scrolling when the viewport is already at the bottom of the
      // document and has space.
      const y = target.offset().top - height
      // Delayed because the initial browser scroll doesn't seem to
      // happen until after the document ready event, so scrolling
      // immediately will be overridden.
      setTimeout(() => scrollTo(0, y), 100)
    }

    // Listen to clicks on hash anchors.
    $('a[href^="#"]').on('click', e => {
      // Stop default scroll. Also stops the automatic URL hash update.
      e.preventDefault()
      // Get the id to scroll to and set the URL hash manually.
      const id = $(e.currentTarget).attr('href').substring(1)
      location.hash = id
      // Use getElementById since the hash may have dots in it.
      const target = $(document.getElementById(id))
      // Scroll to top of target with space for the version warning.
      scrollTo(0, target.offset().top - height)
    })
  }
})
