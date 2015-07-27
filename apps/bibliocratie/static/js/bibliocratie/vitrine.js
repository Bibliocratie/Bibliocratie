$('.play').click(function () {
    //stop the video
    if (!window.isMobile) {
        $('body').addClass('noscroll').append('<div class="previewer"><div><iframe src="//player.vimeo.com/video/113495312?title=0&amp;byline=0&amp;portrait=0&amp;color=000000&amp;autoplay=1" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div><div class="close"></div></div>');

        //pause video
        $('body').addClass('paused');

        $('.previewer').click(function () {
            $('body').removeClass('noscroll');
            $(this).remove();

            //play video back
            $('body').removeClass('paused');
        });
        return false;
    }
});

$('.play2').click(function () {
    //stop the video
    if (!window.isMobile) {
        $('body').addClass('noscroll').append('<div class="previewer"><div><iframe src="//player.vimeo.com/video/111771664?title=0&amp;byline=0&amp;portrait=0&amp;color=ffffff&amp;autoplay=1" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div><div class="close"></div></div>');

        //pause video
        $('body').addClass('paused');

        $('.previewer').click(function () {
            $('body').removeClass('noscroll');
            $(this).remove();

            //play video back
            $('body').removeClass('paused');
        });
        return false;
    }
});

$(document).ready(function() {
    $('#fullpage').scroll(function() {
        if ($('#main').offset().top < -50 ) {
            $("header").removeClass('active').addClass('inactive');
        }
        else{
            $("header").removeClass('inactive').addClass('active');
        }
    });
});
