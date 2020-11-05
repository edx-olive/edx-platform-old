$(document).ready(function () {
  'use strict';

  /**
  * AMAT customization
  * Add error reporting and display errors on UI for video elements.
  * Timeout was set to wait until the video xblock is initialized.
  *
  * Sends generic video error to /report_error enpoint.
  */
  var listenErrors = function () {
    if (!document.querySelector('.studio-xblock-wrapper')) {
      setTimeout(function () {
        var videos = document.querySelectorAll('video')
        videos.forEach(function (video) {
          if (!$(video).parents('.image-explorer-hotspot').length) {
            var sources = video.querySelectorAll('source')
            sources.forEach(function (source) {
              source = $(source)
              if (!source.hasClass('err-listened')) {
                source.on('error', displayError)
                source.addClass('err-listened')
              }
            })
            video = $(video)
            if (!video.hasClass('err-listened')) {
              video.on('error', displayError)
              video.addClass('err-listened')
            }
          }
        })
      }, 100)
    }
  }

  var hide_all_transcripts = function () {
      $('.subtitles').hide()
      $('.wrapper-downloads').hide()
  }

  var displayError = function (event) {
    var target = $(event.target)
    var elementHeight = target.height()
    if (target.parents('video').length > 0) {
      target = target.parents('video')
      elementHeight = target.height()
    }
    if (target.parents('.video-wrapper').length > 0) {
      target = target.parents('.video-wrapper')
    }
    var errorDiv = target.siblings('.video-load-error')
    var transcriptDiv = target.siblings('.subtitles')
    var downloadDiv = target.parent().siblings('.wrapper-downloads')
    var isAdventureXblock = target.parents('div[data-init="AdventureBlock"]').length > 0
    if (errorDiv.length > 0 && !isAdventureXblock) {
      target.hide()
      transcriptDiv.hide()
      downloadDiv.hide()
      if (elementHeight) {
        errorDiv.css('height', elementHeight)
      }
      errorDiv.css('display', 'flex')
      setTimeout(hide_all_transcripts, 2000)
      setTimeout(hide_all_transcripts, 5000)
    }

    if (!isAdventureXblock) {
      var error = 'VideoLoadingError: An error occured for user while loading the video file.'
      $.post('/report_error/', {error: error})
    }
  }

  var displayAll = function () {
    var videos = document.querySelectorAll('.video-wrapper')
    videos.forEach(function (video) { displayAllErrors(video) })
  }

  var displayAllErrors = function (target) {
    target = $(target)
    var elementHeight = target.height()
    var errorDiv = target.siblings('.video-load-error')
    var transcriptDiv = target.siblings('.subtitles')
    var downloadDiv = target.parent().siblings('.wrapper-downloads')
    var isAdventureXblock = target.parents('div[data-init="AdventureBlock"]').length > 0
    if (errorDiv.length > 0 && !isAdventureXblock) {
      target.hide()
      transcriptDiv.hide()
      downloadDiv.hide()
      if (elementHeight) {
        errorDiv.css('height', elementHeight)
      }
      errorDiv.css('display', 'flex')
      setTimeout(hide_all_transcripts, 2000)
      setTimeout(hide_all_transcripts, 5000)
    }
  }

  window.onerror = function (message, source, lineno, colno, error) {
    var target = $(message.target)
    var sources = []
    try {
      sources = [target.find('video')[0].currentSrc, target.find('source')[0].src]
    } catch (error) {
      // skip an error
    }
    if (sources.some(function (src) { return src.indexOf('cloudfront.net') !== -1 })) {
      displayAll()
    }
  }

  listenErrors()
  var seq = $('.sequence')
  if (!seq.hasClass('video-err-listened')) {
    seq.on('sequence:change', listenErrors)
    seq.addClass('video-err-listened')
  }

})
