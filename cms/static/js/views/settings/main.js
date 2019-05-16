define(['js/views/validation','tinymce', 'codemirror', 'underscore', 'jquery', 'jquery.ui', 'js/utils/date_utils',
    'js/models/uploads', 'js/views/uploads', 'js/views/license', 'js/models/license',
    'common/js/components/views/feedback_notification', 'jquery.timepicker', 'date', 'gettext',
    'js/views/learning_info', 'js/views/instructor_info', 'edx-ui-toolkit/js/utils/string-utils'],
       function(ValidatingView, tinymce, CodeMirror, _, $, ui, DateUtils, FileUploadModel,
                FileUploadDialog, LicenseView, LicenseModel, NotificationView,
                timepicker, date, gettext, LearningInfoView, InstructorInfoView, StringUtils) {
           var DetailsView = ValidatingView.extend({
    // Model class is CMS.Models.Settings.CourseDetails
               events: {
                   'input input': 'updateModel',
                   'input textarea': 'updateModel',
        // Leaving change in as fallback for older browsers
                   'change input': 'updateModel',
                   'change textarea': 'updateModel',
                   'change select': 'updateModel',
                   'click .remove-course-introduction-video': 'removeVideo',
                   'focus #course-overview': 'codeMirrorize',
                   'mouseover .timezone': 'updateTime',
        // would love to move to a general superclass, but event hashes don't inherit in backbone :-(
                   'focus :input': 'inputFocus',
                   'blur :input': 'inputUnfocus',
                   'click .action-upload-image': 'uploadImage',
                   'click .add-course-learning-info': 'addLearningFields',
                   'click .add-course-instructor-info': 'addInstructorFields',
                   'click #course-overview-update-btn': 'updateCourseOverview'
               },

               initialize: function(options) {
                   options = options || {};
        // fill in fields
                   this.$el.find('#course-language').val(this.model.get('language'));
                   this.$el.find('#course-organization').val(this.model.get('org'));
                   this.$el.find('#course-number').val(this.model.get('course_id'));
                   this.$el.find('#course-name').val(this.model.get('run'));
                   this.$el.find('.set-date').datepicker({'dateFormat': 'm/d/yy'});

        // Avoid showing broken image on mistyped/nonexistent image
                   this.$el.find('img').error(function() {
                       $(this).hide();
                   });
                   this.$el.find('img').load(function() {
                       $(this).show();
                   });

                   this.listenTo(this.model, 'invalid', this.handleValidationError);
                   this.listenTo(this.model, 'change', this.showNotificationBar);
                   this.selectorToField = _.invert(this.fieldToSelectorMap);
        // handle license separately, to avoid reimplementing view logic
                   this.licenseModel = new LicenseModel({'asString': this.model.get('license')});
                   this.licenseView = new LicenseView({
                       model: this.licenseModel,
                       el: this.$('#course-license-selector').get(),
                       showPreview: true
                   });
                   this.listenTo(this.licenseModel, 'change', this.handleLicenseChange);

                   if (options.showMinGradeWarning || false) {
                       new NotificationView.Warning({
                           title: gettext('Course Credit Requirements'),
                           message: gettext('The minimum grade for course credit is not set.'),
                           closeIcon: true
                       }).show();
                   }

                   this.learning_info_view = new LearningInfoView({
                       el: $('.course-settings-learning-fields'),
                       model: this.model
                   });

                   this.instructor_info_view = new InstructorInfoView({
                       el: $('.course-instructor-details-fields'),
                       model: this.model
                   });

        	  this.$el.find('#' + this.fieldToSelectorMap['mobile']).val(this.model.get('mobile'));
                  if(this.model.get('verified') == 'true')
                  	this.$el.find('#' + this.fieldToSelectorMap['verified']).attr('checked', true);
                  if(this.model.get('pathway') == 'true')
                        this.$el.find('#' + this.fieldToSelectorMap['pathway']).attr('checked', true);
                  if(this.model.get('vr_enabled') == 'true')
                  	this.$el.find('#' + this.fieldToSelectorMap['vr_enabled']).attr('checked', true);

        	  this.$el.find('#' + this.fieldToSelectorMap['yammer']).val(this.model.get('yammer'));
        	  this.$el.find('#' + this.fieldToSelectorMap['level']).val(this.model.get('level'));
                  this.$el.find('#' + this.fieldToSelectorMap['availibility_status']).val(this.model.get('availibility_status'));
        	  this.$el.find('#' + this.fieldToSelectorMap['streams']).val(this.model.get('streams'));
       		  this.$el.find('#' + this.fieldToSelectorMap['tags']).val(this.model.get('tags'));
       	 	  this.$el.find('#' + this.fieldToSelectorMap['objectives']).val(this.model.get('objectives'));
        	  this.$el.find('#' + this.fieldToSelectorMap['course_prerequisites']).val(this.model.get('course_prerequisites'));
        	  this.$el.find('#' + this.fieldToSelectorMap['instructors']).val(this.model.get('instructors'));
        	  this.$el.find('#' + this.fieldToSelectorMap['instructor_designers']).val(this.model.get('instructor_designers'));
        	  this.$el.find('#' + this.fieldToSelectorMap['standard']).val(this.model.get('standard'));
        	  this.$el.find('#' + this.fieldToSelectorMap['price']).val(this.model.get('price'));

               },

               render: function() {
        // Clear any image preview timeouts set in this.updateImagePreview
                   clearTimeout(this.imageTimer);

                   DateUtils.setupDatePicker('start_date', this);
                   DateUtils.setupDatePicker('end_date', this);
                   DateUtils.setupDatePicker('enrollment_start', this);
                   DateUtils.setupDatePicker('enrollment_end', this);

                   this.$el.find('#' + this.fieldToSelectorMap['overview']).val(this.model.get('overview'));
                   this.codeMirrorize(null, $('#course-overview')[0]);

                   if (this.model.get('title') !== '') {
                       this.$el.find('#' + this.fieldToSelectorMap.title).val(this.model.get('title'));
                   } else {
                       var displayName = this.$el.find('#' + this.fieldToSelectorMap.title).attr('data-display-name');
                       this.$el.find('#' + this.fieldToSelectorMap.title).val(displayName);
                   }
                   this.$el.find('#' + this.fieldToSelectorMap.subtitle).val(this.model.get('subtitle'));
                   this.$el.find('#' + this.fieldToSelectorMap.duration).val(this.model.get('duration'));
                   this.$el.find('#' + this.fieldToSelectorMap.description).val(this.model.get('description'));

                   this.$el.find('#' + this.fieldToSelectorMap['short_description']).val(this.model.get('short_description'));

                   this.$el.find('.current-course-introduction-video iframe').attr('src', this.model.videosourceSample());
                   this.$el.find('#' + this.fieldToSelectorMap['intro_video']).val(this.model.get('intro_video') || '');
                   if (this.model.has('intro_video')) {
                       this.$el.find('.remove-course-introduction-video').show();
                   }
                   else this.$el.find('.remove-course-introduction-video').hide();

                   this.$el.find('#' + this.fieldToSelectorMap['effort']).val(this.model.get('effort'));

                   var courseImageURL = this.model.get('course_image_asset_path');
                   this.$el.find('#course-image-url').val(courseImageURL);
                   this.$el.find('#course-image').attr('src', courseImageURL);

                   var bannerImageURL = this.model.get('banner_image_asset_path');
                   this.$el.find('#banner-image-url').val(bannerImageURL);
                   this.$el.find('#banner-image').attr('src', bannerImageURL);

                   var videoThumbnailImageURL = this.model.get('video_thumbnail_image_asset_path');
                   this.$el.find('#video-thumbnail-image-url').val(videoThumbnailImageURL);
                   this.$el.find('#video-thumbnail-image').attr('src', videoThumbnailImageURL);

                   var pre_requisite_courses = this.model.get('pre_requisite_courses');
                   pre_requisite_courses = pre_requisite_courses.length > 0 ? pre_requisite_courses : '';
                   this.$el.find('#' + this.fieldToSelectorMap['pre_requisite_courses']).val(pre_requisite_courses);

                   if (this.model.get('entrance_exam_enabled') == 'true') {
                       this.$('#' + this.fieldToSelectorMap['entrance_exam_enabled']).attr('checked', this.model.get('entrance_exam_enabled'));
                       this.$('.div-grade-requirements').show();
                   }
                   else {
                       this.$('#' + this.fieldToSelectorMap['entrance_exam_enabled']).removeAttr('checked');
                       this.$('.div-grade-requirements').hide();
                   }
                   this.$('#' + this.fieldToSelectorMap['entrance_exam_minimum_score_pct']).val(this.model.get('entrance_exam_minimum_score_pct'));

                   var selfPacedButton = this.$('#course-pace-self-paced'),
                       instructorPacedButton = this.$('#course-pace-instructor-paced'),
                       paceToggleTip = this.$('#course-pace-toggle-tip');
                   (this.model.get('self_paced') ? selfPacedButton : instructorPacedButton).attr('checked', true);
                   if (this.model.canTogglePace()) {
                       selfPacedButton.removeAttr('disabled');
                       instructorPacedButton.removeAttr('disabled');
                       paceToggleTip.text('');
                   }
                   else {
                       selfPacedButton.attr('disabled', true);
                       instructorPacedButton.attr('disabled', true);
                       paceToggleTip.text(gettext('Course pacing cannot be changed once a course has started.'));
                   }

                   this.licenseView.render();
                   this.learning_info_view.render();
                   this.instructor_info_view.render();

                   return this;
               },
               fieldToSelectorMap: {
                   'language': 'course-language',
                   'start_date': 'course-start',
                   'end_date': 'course-end',
                   'enrollment_start': 'enrollment-start',
                   'enrollment_end': 'enrollment-end',
                   'overview': 'course-overview',
                   'title': 'course-title',
                   'subtitle': 'course-subtitle',
                   'duration': 'course-duration',
                   'description': 'course-description',
                   'short_description': 'course-short-description',
                   'intro_video': 'course-introduction-video',
                   'effort': 'course-effort',
                   'course_image_asset_path': 'course-image-url',
                   'banner_image_asset_path': 'banner-image-url',
                   'video_thumbnail_image_asset_path': 'video-thumbnail-image-url',
                   'pre_requisite_courses': 'pre-requisite-course',
                   'entrance_exam_enabled': 'entrance-exam-enabled',
                   'entrance_exam_minimum_score_pct': 'entrance-exam-minimum-score-pct',
                   'course_settings_learning_fields': 'course-settings-learning-fields',
                   'add_course_learning_info': 'add-course-learning-info',
                   'add_course_instructor_info': 'add-course-instructor-info',
                   'course_learning_info': 'course-learning-info',

                   'mobile': 'appliedx-custom-mobile',
                   'pathway': 'appliedx-custom-pathway',
                   'verified': 'appliedx-custom-verified',
                   'vr_enabled': 'appliedx-custom-vr_enabled',
                   'yammer': 'appliedx-custom-yammer',
                   'level': 'appliedx-custom-level',
                   'availibility_status': 'appliedx-custom-availibility_status',
                   'streams': 'appliedx-custom-streams',
                   'tags': 'appliedx-custom-tags',
                   'objectives': 'appliedx-custom-objectives',
                   'course_prerequisites': 'appliedx-custom-course_prerequisites',
                   'instructors': 'appliedx-custom-instructors',
                   'instructor_designers': 'appliedx-custom-instructor_designers',
                   'standard': 'appliedx-custom-standard',
                   'price': 'appliedx-custom-price',
               },

               addLearningFields: function() {
        /*
        * Add new course learning fields.
        * */
                   var existingInfo = _.clone(this.model.get('learning_info'));
                   existingInfo.push('');
                   this.model.set('learning_info', existingInfo);
               },

               addInstructorFields: function() {
        /*
        * Add new course instructor fields.
        * */
                   var instructors = this.model.get('instructor_info').instructors.slice(0);
                   instructors.push({
                       name: '',
                       title: '',
                       organization: '',
                       image: '',
                       bio: ''
                   });
                   this.model.set('instructor_info', {instructors: instructors});
               },

               updateTime: function(e) {
                   var now = new Date(),
                       hours = now.getUTCHours(),
                       minutes = now.getUTCMinutes(),
                       currentTimeText = StringUtils.interpolate(
                gettext('{hours}:{minutes} (current UTC time)'),
                           {
                               'hours': hours,
                               'minutes': minutes
                           }
            );

                   $(e.currentTarget).attr('title', currentTimeText);
               },
               updateCourseOverview: function(event){
               event.preventDefault();
                 $("#new_course_overview_hidden").empty();
                 var course_overview_description = this.model.get('short_description');
                 var learning_objectives = JSON.parse(this.model.get('objectives'));
                 var course_prerequisites = JSON.parse(this.model.get('course_prerequisites'));
                 var instructors = JSON.parse(this.model.get('instructors'));
                 var instructor_designers = JSON.parse(this.model.get('instructor_designers'));
                 var new_course_overview = '<section class="course-description">\
                                             <h2 class="main-header" style="font-family: helvetica;font-size: 1.5rem;color: #00ccff;"> About This Course </h2> \
                                              '+course_overview_description+' \
                                            </section>'


                 if (learning_objectives != '' || learning_objectives.length != 0 )
                 {
                    var learning_objectives_html = '';
                    $.each(learning_objectives, function( index, value ) {
                      learning_objectives_html+='<li>'+value+'</li>'
                    });

                    new_course_overview+='<section class="learning-objectives"> \
                                                <h2 class="main-header" style="font-family: helvetica;font-size: 1.5rem;color: #00ccff;"> You Will Learn To</h2> <ul>'+learning_objectives_html+'\
                                               </ul></section>'
                 }
                 if (course_prerequisites != '' || course_prerequisites.length != 0){
                    var course_prerequisites_html = '';
                    $.each(course_prerequisites, function( index, value ) {
                      course_prerequisites_html+='<li>'+value+'</li>'
                    });

                    new_course_overview+='<section class="pre-requisites"> <h2 class="main-header" style="font-family: helvetica;font-size: 1.5rem;color: #00ccff;"> Pre-requisites </h2> <ul>'+course_prerequisites_html+' </ul></section>'
                 }
                 else{

                    console.log("No pre-requisites");
                 }
                if((instructors != '' || instructors.length !=0) || (instructor_designers != '' || instructor_designers.length != 0)){

		new_course_overview+='<section class="appliedx-course-staff">\
                    <h2 class="main-header" style="font-family: helvetica;font-size: 1.5rem;color: #00ccff;"> Course Staff </h2>\
                    <section class="course-staff-instructor" style="display:none"><h3 class="sub-header" style="display:none;font-family: helvetica;font-size: 1rem;color: #00ccff;"> Instructors </h3></section>\
                    <section class="course-staff-instructional-designer" style="display:none"><h3 class="sub-header" style="display:none;font-family: helvetica;font-size: 1rem;color: #00ccff;"> Instructional Designer </h3></section>\
                    </section>';

                  $("#new_course_overview_hidden").append(new_course_overview)

                if(instructors != '' || instructors.length != 0 ){
                $(".course-staff-instructor").css('display','block');
                $.each( instructors, function( key, value ) {
                  $.ajax({
                    url: "https://services.appliedx.amat.com/appliedx_controls/instructor_details/",
                    type: "get", //send it through get method
                    data: {
                      name: value
                    },
                    dataType: "json",
                    success: function(response) {
                      var instructor = response[0]
                      var instructor_image = ( instructor.image_url == null || instructor.image_url == "" ) ? "https://cdn4.iconfinder.com/data/icons/ui-standard/96/People-512.png" : instructor.image_url;
                      var instructor_html ='<div style="min-height:150px;margin-bottom:10px;"><span><img src="'+ instructor_image +'" style="max-width:150px;float:left;position:relative;margin-right:15px;"></span><span class="name" style="font-weight:600;font-size: 19px;">'+instructor.name+'</span><br><span class="description" style="font-size:16px;">'+instructor.description+'</span></div><hr></br>'
                      $(".course-staff-instructor").append(instructor_html);
                  new_course_overview = $("#new_course_overview_hidden").html()
                  tinymce.get('course-overview').setContent(new_course_overview);

                    },
                    error: function(xhr) {
                      console.log("Error in fetching instructors")
                      console.log(xhr)
                    }
                    //complete: function(){
                    //updateCourseStaff();
                    //}
                  });
                });

                }
               else{
                   console.log("No Instructors");
                  tinymce.get('course-overview').setContent(new_course_overview);
               }

                if (instructor_designers != '' || instructor_designers.length != 0){
                $(".course-staff-instructional-designer").css('display','block');
                $.each( instructor_designers, function( key, value ) {
                  $.ajax({
                    url: "https://services.appliedx.amat.com/appliedx_controls/instructor_details/",
                    type: "get", //send it through get method
                    data: {
                      name: value
                    },
                    dataType: "json",
                    success: function(response) {
                      var instructor_designer = response[0]
                      var instructor_designer_image = ( instructor_designer.image_url == null ||  instructor_designer.image_url == "" ) ? "https://cdn4.iconfinder.com/data/icons/ui-standard/96/People-512.png" : instructor_designer.image_url;
                      var instructor_designer_html='<div style="min-height:150px;margin-bottom:10px;"><span><img src="'+instructor_designer_image +'" style="max-width:150px;float:left;position:relative;margin-right:15px;"></span><span class="name" style="font-weight:600;font-size: 19px;">'+instructor_designer.name+'</span><br><span class="description" style="font-size:16px;">'+instructor_designer.description+'</span></div><hr></br>'
                      $(".course-staff-instructional-designer").append(instructor_designer_html);
                  new_course_overview = $("#new_course_overview_hidden").html()
                  tinymce.get('course-overview').setContent(new_course_overview);

                    },
                    error: function(xhr) {
                      console.log("Error in fetching instructional designer")
                      console.log(xhr)
                    }
                    //complete: function(){
                     // updateCourseStaff();
                   // }

                  });
                });

                }
                else{
                    console.log("No Instructors Designer");
                }
               }
                  else{
                  tinymce.get('course-overview').setContent(new_course_overview);
                  }


               //function updateCourseStaff(event){
                //  event.preventDefault();
                //}
               },
               updateModel: function(event) {
                   var value;
                   var index = event.currentTarget.getAttribute('data-index');
                   switch (event.currentTarget.id) {
                   case 'course-learning-info-' + index:
                       value = $(event.currentTarget).val();
                       var learningInfo = this.model.get('learning_info');
                       learningInfo[index] = value;
                       this.showNotificationBar();
                       break;
                   case 'course-instructor-name-' + index:
                   case 'course-instructor-title-' + index:
                   case 'course-instructor-organization-' + index:
                   case 'course-instructor-bio-' + index:
                       value = $(event.currentTarget).val();
                       var field = event.currentTarget.getAttribute('data-field'),
                           instructors = this.model.get('instructor_info').instructors.slice(0);
                       instructors[index][field] = value;
                       this.model.set('instructor_info', {instructors: instructors});
                       this.showNotificationBar();
                       break;
                   case 'course-instructor-image-' + index:
                       instructors = this.model.get('instructor_info').instructors.slice(0);
                       instructors[index].image = $(event.currentTarget).val();
                       this.model.set('instructor_info', {instructors: instructors});
                       this.showNotificationBar();
                       this.updateImagePreview(event.currentTarget, '#course-instructor-image-preview-' + index);
                       break;
                   case 'course-image-url':
                       this.updateImageField(event, 'course_image_name', '#course-image');
                       break;
                   case 'banner-image-url':
                       this.updateImageField(event, 'banner_image_name', '#banner-image');
                       break;
                   case 'video-thumbnail-image-url':
                       this.updateImageField(event, 'video_thumbnail_image_name', '#video-thumbnail-image');
                       break;
                   case 'entrance-exam-enabled':
                       if ($(event.currentTarget).is(':checked')) {
                           this.$('.div-grade-requirements').show();
                       } else {
                           this.$('.div-grade-requirements').hide();
                       }
                       this.setField(event);
                       break;
                   case 'entrance-exam-minimum-score-pct':
            // If the val is an empty string then update model with default value.
                       if ($(event.currentTarget).val() === '') {
                           this.model.set('entrance_exam_minimum_score_pct', this.model.defaults.entrance_exam_minimum_score_pct);
                       }
                       else {
                           this.setField(event);
                       }
                       break;
                   case 'pre-requisite-course':
                       var value = $(event.currentTarget).val();
                       value = value == '' ? [] : [value];
                       this.model.set('pre_requisite_courses', value);
                       break;
        // Don't make the user reload the page to check the Youtube ID.
        // Wait for a second to load the video, avoiding egregious AJAX calls.
                   case 'course-introduction-video':
                       this.clearValidationErrors();
                       var previewsource = this.model.set_videosource($(event.currentTarget).val());
                       clearTimeout(this.videoTimer);
                       this.videoTimer = setTimeout(_.bind(function() {
                           this.$el.find('.current-course-introduction-video iframe').attr('src', previewsource);
                           if (this.model.has('intro_video')) {
                               this.$el.find('.remove-course-introduction-video').show();
                           }
                           else {
                               this.$el.find('.remove-course-introduction-video').hide();
                           }
                       }, this), 1000);
                       break;
                   case 'course-pace-self-paced':
            // Fallthrough to handle both radio buttons
                   case 'course-pace-instructor-paced':
                       this.model.set('self_paced', JSON.parse(event.currentTarget.value));
                       break;
                   case 'course-language':
                   case 'course-effort':
                   case 'course-title':
                   case 'course-subtitle':
                   case 'course-duration':
                   case 'course-description':
                   case 'course-short-description':
                        this.setField(event);
                        break;


        	   case 'appliedx-custom-mobile':
            		this.setField(event);
            		break;
                   case 'appliedx-custom-pathway':
                        this.setField(event);
                        break;
        	   case 'appliedx-custom-verified':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-vr_enabled':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-yammer':
            		this.setField(event);
            		break;
                   case 'appliedx-custom-availibility_status':
                        this.setField(event);
                        break;
        	   case 'appliedx-custom-level':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-streams':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-tags':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-objectives':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-course_prerequisites':
            		this.setField(event);
            		break;
         	   case 'appliedx-custom-instructors':
            		this.setField(event);
            		break;
        	   case 'appliedx-custom-instructor_designers':
            		this.setField(event);
            		break;
	          case 'appliedx-custom-standard':
                        this.setField(event);
                        break;
      		  case 'appliedx-custom-price':
                        this.setField(event);
                        break;

                  case 'course-overview-update-btn':
                        break;
                   default: // Everything else is handled by datepickers and CodeMirror.
                       break;
                   }
               },
               updateImageField: function(event, image_field, selector) {
                   this.setField(event);
                   var url = $(event.currentTarget).val();
                   var image_name = _.last(url.split('/'));
        // If image path is entered directly, we need to strip the asset prefix
                   image_name = _.last(image_name.split('block@'));
                   this.model.set(image_field, image_name);
                   this.updateImagePreview(event.currentTarget, selector);
               },
               updateImagePreview: function(imagePathInputElement, previewSelector) {
        // Wait to set the image src until the user stops typing
                   clearTimeout(this.imageTimer);
                   this.imageTimer = setTimeout(function() {
                       $(previewSelector).attr('src', $(imagePathInputElement).val());
                   }, 1000);
               },
               removeVideo: function(event) {
                   event.preventDefault();
                   if (this.model.has('intro_video')) {
                       this.model.set_videosource(null);
                       this.$el.find('.current-course-introduction-video iframe').attr('src', '');
                       this.$el.find('#' + this.fieldToSelectorMap['intro_video']).val('');
                       this.$el.find('.remove-course-introduction-video').hide();
                   }
               },
               codeMirrors: {},
               codeMirrorize: function(e, forcedTarget) {
                   var thisTarget, cachethis, field, cmTextArea;
                   if (forcedTarget) {
                       thisTarget = forcedTarget;
                       thisTarget.id = $(thisTarget).attr('id');
                   } else if (e !== null) {
                       thisTarget = e.currentTarget;
                   } else
        {
            // e and forcedTarget can be null so don't deference it
            // This is because in cases where we have a marketing site
            // we don't display the codeMirrors for editing the marketing
            // materials, except we do need to show the 'set course image'
            // workflow. So in this case e = forcedTarget = null.
                       return;
                   }
/*
                   if (!this.codeMirrors[thisTarget.id]) {
                       cachethis = this;
                       field = this.selectorToField[thisTarget.id];
                       this.codeMirrors[thisTarget.id] = CodeMirror.fromTextArea(thisTarget, {
                           mode: 'text/html', lineNumbers: true, lineWrapping: true});
                       this.codeMirrors[thisTarget.id].on('change', function(mirror) {
                           mirror.save();
                           cachethis.clearValidationErrors();
                           var newVal = mirror.getValue();
                           if (cachethis.model.get(field) != newVal) {
                               cachethis.setAndValidate(field, newVal);
                           }
                       });
                       cmTextArea = this.codeMirrors[thisTarget.id].getInputField();
                       cmTextArea.setAttribute('id', 'course-overview-cm-textarea');
                   }
               },

               revertView: function() {
        // Make sure that the CodeMirror instance has the correct
        // data from its corresponding textarea
                   var self = this;
                   this.model.fetch({
                       success: function() {
                           self.render();
                           _.each(self.codeMirrors, function(mirror) {
                               var ele = mirror.getTextArea();
                               var field = self.selectorToField[ele.id];
                               mirror.setValue(self.model.get(field));
                           });
                           self.licenseModel.setFromString(self.model.get('license'), {silent: true});
                           self.licenseView.render();
                       },
                       reset: true,
                       silent: true});
               },
*/

               if (!this.codeMirrors[thisTarget.id]) {
            var cachethis = this;
            var field = this.selectorToField[thisTarget.id];
            this.codeMirrors[thisTarget.id]=thisTarget.id;
            tinyMCE.baseURL = "" + baseUrl + "/js/vendor/tinymce/js/tinymce";
            tinyMCE.suffix = ".min";
            // this.codeMirrors[thisTarget.id] = CodeMirror.fromTextArea(thisTarget, {
               // mode: "text/html", lineNumbers: true, lineWrapping: true});
            tinymce.init({ selector: '#' + thisTarget.id,
                script_url: "" + baseUrl + "/js/vendor/tinymce/js/tinymce/tinymce.full.min.js",
                theme: "modern",
                skin: 'studio-tmce4',
                 schema: "html5",
                  convert_urls: false,
                  formats: {
                    code: {
                      inline: 'code'
                   }
                 },
                 width: '100%',
                 height: '400px',
                menubar: false,
                statusbar: false,
                visual: false,
                plugins: "textcolor, link, image, codemirror",
                codemirror: {
                        path: "" + baseUrl + "/js/vendor"
                },
                image_advtab: true,
                toolbar: "formatselect | fontselect | bold italic underline forecolor wrapAsCode | bullist numlist outdent indent blockquote | link unlink image | code",
                init_instance_callback: function(editor){
                        editor.on('SetContent', function(e){
                        newVal = editor.getContent();
                        cachethis.clearValidationErrors();
                        if (cachethis.model.get(field) != newVal) {
                                cachethis.setAndValidate(field, newVal); }
                        });
                        editor.on('KeyUp', function(e){
                        newVal = editor.getContent();
                        cachethis.clearValidationErrors();
                        if (cachethis.model.get(field) != newVal) {
                                cachethis.setAndValidate(field, newVal); }
                        });

                }
                });
            // tinymce.get(thisTarget)this.model.get
            // this.codeMirrors[thisTarget.id].on('change', function (mirror) {
                   // mirror.save();
                   // cachethis.clearValidationErrors();
                   // var newVal = mirror.getValue();
                   // if (cachethis.model.get(field) != newVal) {
                   // cachethis.setAndValidate(field, newVal);
                    //}
            //});
        }
    },
    revertView: function() {
        // Make sure that the CodeMirror instance has the correct
        // data from its corresponding textarea
        var self = this;
        this.model.fetch({
            success: function() {
                self.render();
                // _.each(self.codeMirrors, function(values,key) {
                    // var ele = mirror.getTextArea();
                    // var field = self.selectorToField[values];
                    // var field = self.selectorToField[values];
                     //tinymce.init({ selector : '#course-overview' };
                    // tinymce.get(self.codeMirrors[values]).setContent(self.model.get(field));
                    // mirror.setValue(self.model.get(field));
                // });
                self.licenseModel.setFromString(self.model.get("license"), {silent: true});
                self.licenseView.render()
            },
            reset: true,
            silent: true});
    },


              setAndValidate: function(attr, value) {
        // If we call model.set() with {validate: true}, model fields
        // will not be set if validation fails. This puts the UI and
        // the model in an inconsistent state, and causes us to not
        // see the right validation errors the next time validate() is
        // called on the model. So we set *without* validating, then
        // call validate ourselves.
                   this.model.set(attr, value);
                   this.model.isValid();
               },

               showNotificationBar: function() {
        // We always call showNotificationBar with the same args, just
        // delegate to superclass
                   ValidatingView.prototype.showNotificationBar.call(this,
                                                          this.save_message,
                                                          _.bind(this.saveView, this),
                                                          _.bind(this.revertView, this));
               },

               uploadImage: function(event) {
                   event.preventDefault();
                   var title = '', selector = '', image_key = '', image_path_key = '';
                   switch (event.currentTarget.id) {
                   case 'upload-course-image':
                       title = gettext('Upload your course image.');
                       selector = '#course-image';
                       image_key = 'course_image_name';
                       image_path_key = 'course_image_asset_path';
                       break;
                   case 'upload-banner-image':
                       title = gettext('Upload your banner image.');
                       selector = '#banner-image';
                       image_key = 'banner_image_name';
                       image_path_key = 'banner_image_asset_path';
                       break;
                   case 'upload-video-thumbnail-image':
                       title = gettext('Upload your video thumbnail image.');
                       selector = '#video-thumbnail-image';
                       image_key = 'video_thumbnail_image_name';
                       image_path_key = 'video_thumbnail_image_asset_path';
                       break;
                   }

                   var upload = new FileUploadModel({
                       title: title,
                       message: gettext('Files must be in JPEG or PNG format.'),
                       mimeTypes: ['image/jpeg', 'image/png']
                   });
                   var self = this;
                   var modal = new FileUploadDialog({
                       model: upload,
                       onSuccess: function(response) {
                           var options = {};
                           options[image_key] = response.asset.display_name;
                           options[image_path_key] = response.asset.url;
                           self.model.set(options);
                           self.render();
                           $(selector).attr('src', self.model.get(image_path_key));
                       }
                   });
                   modal.show();
               },

               handleLicenseChange: function() {
                   this.showNotificationBar();
                   this.model.set('license', this.licenseModel.toString());
               }
           });

           return DetailsView;
       }); // end define()
