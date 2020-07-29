(function(undefined) {
    'use strict';

  var videos = document.querySelectorAll('video')
  videos.forEach(function (video) {
    var sources = video.querySelectorAll('source')
    sources.forEach(function (source) {
      $(source).on('error', displayError)
    })
    $(video).on('error', displayError)
  })

  var displayError = function (event) {
    var target = $(event.target)
    if (target.parents('.video-wrapper').length > 0) {
      target = target.parents('.video-wrapper')
    } else if (target.parents('video').length > 0) {
      target = target.parents('video')
    }
    var errorDiv = target.siblings('.video-load-error')
    target.hide()
    errorDiv.css('display', 'flex')
  }
}).call(this);
