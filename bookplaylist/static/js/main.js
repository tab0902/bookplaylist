$(function() {

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
      } else {
        $('#dummy').fadeOut()
        $('#drawer').animate({height: 'toggle'}, function() {
          $('#content').removeClass('fixed').css('top', height)
          $('body,html').animate({scrollTop: scrollpos}, 0)
        })
      }
    }
    return false
  })

  // delete/restore book button
  $('.delete-book').on('click', function(e) {
    const book_id = $(this).attr('data-book')
    const $item = $('.playlist-form-book-item[data-book='+book_id+']')
    const $itemDelete = $('.playlist-form-book-delete[data-book='+book_id+']')
    const $deleteInput = $item.find('.delete-input')
    $deleteInput.val('on')
    $item.fadeOut(400, function() {
      $itemDelete.fadeIn()
    })
  })
  $('.restore-book').on('click', function(e) {
    const book_id = $(this).attr('data-book')
    const $item = $('.playlist-form-book-item[data-book='+book_id+']')
    const $itemDelete = $('.playlist-form-book-delete[data-book='+book_id+']')
    const $deleteInput = $item.find('.delete-input')
    $deleteInput.val('')
    $itemDelete.fadeOut(400, function() {
      $item.fadeIn()
    })
  })
  $(document).ready(function() {
    $('.playlist-form-book-item').each(function(i, o) {
      const book_id = $(o).attr('data-book')
      const $deleteInput = $(o).find('.delete-input')
      const $itemDelete = $('.playlist-form-book-delete[data-book='+book_id+']')
      if ($deleteInput.val()) {
        $(o).hide()
        $itemDelete.show()
      }
    })
  })

  // prevent duplicate submit
  $('form').submit(function() {
    const selector = ':submit:not(.allow-duplicate)'
    $(selector, this).prop('disabled', true)
    $(selector, this).css('opacity', 1)
    setTimeout(function() {
      $(selector, this).prop('disabled', false)
    }, 10000)
  })

  // toggle loading spinner
  $('.search-form').submit(function() {
    $('.search-loading').show()
    $('.search-results').hide()
  })
})
