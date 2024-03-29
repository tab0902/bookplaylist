// function to get url params
function getUrlParams() {
  let params = new Object
  const elms = location.search.substring(1).split('&')
  for(let i = 0; elms[i]; i++) {
      const k = elms[i].split('=')
      params[k[0]] = k[1]
  }
  return params
}

// function for ajax form
function csrfSafeMethod(method) {
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))
}

// identify user agent
function get_user_agent() {
  const ua = navigator.userAgent
  if (ua.indexOf('iPhone') > 0 || ua.indexOf('iPod') > 0 || ua.indexOf('Android') > 0 && ua.indexOf('Mobile') > 0) {
    return 'sp'
  } else if (ua.indexOf('iPad') > 0 || ua.indexOf('Android') > 0) {
    return 'tab'
  } else {
    return 'pc'
  }
}

$(function() {

  // Lazy Load
  $('img.lazy').lazyload({
    skip_invisible: true
  })

  // drawer menu
  let height
  let scrollpos
  let header = $('#header').height()

  $('#dummy').css('height', 99999)
  $('#drawer').css('padding-top', header)
  $('#content').css('padding-top', header)

  $('#hamburger').on('click', function() {
    if (!$('#drawer').is(':animated')) {
      $(this).toggleClass('active')
      if ($(this).hasClass('active')) {
        scrollpos = $(window).scrollTop()
        height = scrollpos - header
        $('#dummy').fadeIn()
        $('#drawer').animate({height: 'toggle'})
        $('#content').addClass('fixed').css('top', -scrollpos)
        $('#footer').hide()
      } else {
        $('#dummy').fadeOut()
        $('#drawer').animate({height: 'toggle'}, function() {
          $('#footer').show()
          $('#content').removeClass('fixed').css('top', height)
          $('body,html').animate({scrollTop: scrollpos}, 0)
        })
      }
    }
    return false
  })

  // wrap selectbox
  $('select').wrap('<div class="select-wrapper">')

  // prevent duplicate submit
  $('form').on('submit', function() {
    const selector = ':submit:not(.allow-duplicate)'
    if (!$(this).hasClass('allow-duplicate') && !$(this).has('#ajax-form')) {
      $(selector, this).prop('disabled', true)
      $(selector, this).css('opacity', 1)
      setTimeout(function() {
        $(selector, this).prop('disabled', false)
      }, 10000)
    }
  })

  // delete/restore book button
  $('.delete-book').on('click', function(e) {
    const isbn = $(this).attr('data-isbn')
    const $item = $('.playlist-form-book-item[data-isbn='+isbn+']')
    const $itemDelete = $('.playlist-form-book-delete[data-isbn='+isbn+']')
    const $deleteInput = $item.find('.delete-input')
    $deleteInput.val('on')
    $item.fadeOut(400, function() {
      $itemDelete.fadeIn()
    })
  })
  $('.restore-book').on('click', function(e) {
    const isbn = $(this).attr('data-isbn')
    const $item = $('.playlist-form-book-item[data-isbn='+isbn+']')
    const $itemDelete = $('.playlist-form-book-delete[data-isbn='+isbn+']')
    const $deleteInput = $item.find('.delete-input')
    $deleteInput.val('')
    $itemDelete.fadeOut(400, function() {
      $item.fadeIn()
    })
  })
  $(document).ready(function() {
    $('.playlist-form-book-item').each(function(i, o) {
      const isbn = $(o).attr('data-isbn')
      const $deleteInput = $(o).find('.delete-input')
      const $itemDelete = $('.playlist-form-book-delete[data-isbn='+isbn+']')
      if ($deleteInput.val()) {
        $(o).hide()
        $itemDelete.show()
      }
    })
  })

  // profile edit button
  $('.profile-edit-btn').on('click', function() {
    $(this).hide()
    $('#profile-info').hide()
    $('#profile-form').show()
  })
  $('.profile-edit-cancel').on('click', function() {
    $('#profile-form').hide()
    $('#profile-info').show()
    $('.profile-edit-btn').show()
  })
})
