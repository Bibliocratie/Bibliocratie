module.exports = function(grunt) {
    grunt.initConfig({
        less: {
            development: {
                options: {
                    paths: ["./apps/bibliocratie/static/less"],
                    yuicompress: true
                },
                files: {
                    "./apps/bibliocratie/static/css/main.css": "./apps/bibliocratie/static/less/main.less"
                }
            }
        },
        watch: {
            files: "./apps/bibliocratie/static/less/*",
            tasks: ["less"]
        }
    });
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.registerTask('default','watch');
};
