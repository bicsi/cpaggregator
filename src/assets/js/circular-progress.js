$(function() {

  $(".progress").each(function() {

    var value = $(this).attr('data-value');
    var max_value = $(this).attr('data-max-value') || 1.;
    value /= max_value;

    var left = $(this).find('.progress-left .progress-bar');
    var right = $(this).find('.progress-right .progress-bar');

    if (value > 0) {
      if (value <= .5) {
        right.css('transform', 'rotate(' + percentageToDegrees(value) + 'deg)')
      } else {
        right.css('transform', 'rotate(180deg)')
        left.css('transform', 'rotate(' + percentageToDegrees(value - .5) + 'deg)')
      }
    }

  })

  function percentageToDegrees(percentage) {

    return percentage * 360

  }

});