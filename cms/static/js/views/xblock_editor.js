/**
 * XBlockEditorView displays the authoring view of an xblock, and allows the user to switch between
 * the available modes.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/xblock', 'js/views/metadata', 'js/collections/metadata',
        'jquery.inputnumber'],
    function($, _, gettext, XBlockView, MetadataView, MetadataCollection) {
        var XBlockEditorView = XBlockView.extend({
            // takes XBlockInfo as a model

            options: $.extend({}, XBlockView.prototype.options, {
                view: 'studio_view'
            }),

            initialize: function() {
                XBlockView.prototype.initialize.call(this);
                this.view = this.options.view;
            },

            xblockReady: function(xblock) {
                XBlockView.prototype.xblockReady.call(this, xblock);
                this.initializeEditors();
            },

            initializeEditors: function() {
                var metadataEditor,
                    defaultMode = 'editor';
                metadataEditor = this.createMetadataEditor();
                this.metadataEditor = metadataEditor;
                if (!this.hasCustomTabs()) {
                    if (this.getDataEditor()) {
                        defaultMode = 'editor';
                    } else if (metadataEditor) {
                        defaultMode = 'settings';
                    }
                    this.selectMode(defaultMode);
                }
            },

            getDefaultModes: function() {
                return [
                    {id: 'editor', name: gettext('Editor')},
                    {id: 'settings', name: gettext('Settings')}
                ];
            },

            hasCustomTabs: function() {
                return this.$('.editor-with-tabs').length > 0;
            },

            hasCustomButtons: function() {
                return this.$('.editor-with-buttons').length > 0;
            },

            createMetadataEditor: function() {
                var metadataEditor,
                    metadataData,
                    videoLocatorsEl,
                    models = [],
                    key,
                    xblock = this.xblock,
                    metadataView = null;
                    metadataEditor = this.$('.metadata_edit');
                if (metadataEditor.length === 1) {
                    metadataData = metadataEditor.data('metadata');
                    for (key in metadataData) {
                        if (metadataData.hasOwnProperty(key)) {
                            models.push(metadataData[key]);
                        }
                    }
                    metadataView = new MetadataView.Editor({
                        el: metadataEditor,
                        collection: new MetadataCollection(models)
                    });
                    if (xblock.setMetadataEditor) {
                        xblock.setMetadataEditor(metadataView);
                    }
                    videoLocatorsEl = $('li span:contains("Video locators")').closest('li.metadata_entry');
                    if (videoLocatorsEl.length) {
                        videoLocatorsEl.addClass('hidden');
                    }
                }
                return metadataView;
            },

            getDataEditor: function() {
                var editor = this.$('.wrapper-comp-editor');
                return editor.length === 1 ? editor : null;
            },

            getMetadataEditor: function() {
                return this.metadataEditor;
            },

            /**
             * Returns the updated field data for the xblock. Note that this works for all
             * XModules as well as for XBlocks that provide a 'collectFieldData' API.
             */
            getXBlockFieldData: function() {
                var xblock = this.xblock, // HTMLEditingDescriptor
                    metadataEditor = this.getMetadataEditor(),
                    data = null,
                    iframes = [];
                // If the xblock supports returning its field data then collect it
                if (xblock.collectFieldData) {
                    data = xblock.collectFieldData();
                // ... else if this is an XModule then call its save method
                } else if (xblock.save) {
                    data = xblock.save();
                    if (xblock.type === 'static_tab') {
                        var videoLocators = $('.metadata_edit').data('metadata').video_locators.value;
                        if (document.querySelector(".modal-editor iframe") !== null) {
                          iframes = document.querySelector(".modal-editor iframe").contentWindow.document.querySelectorAll("iframe[data-locator]");
                        } else {
                          var parser = new DOMParser();
                          var htmlDoc = parser.parseFromString(document.querySelector(".modal-editor .edit-box").textContent, 'text/html');
                          iframes = htmlDoc.querySelectorAll("iframe[data-locator]");
                        }
                          var iframesLocators = [];
                          iframes.forEach(function(iframe) {
                              iframesLocators.push(iframe.dataset.locator);
                          });
                          if (iframesLocators.length < videoLocators.length) {
                              videoLocators.forEach(function(loc) {
                                  if (!iframesLocators.includes(loc)) {
                                      videoLocators.pop(loc);
                                      $(`[data-usage-id='${loc}']`).siblings(".wrapper.wrapper-component-action-header").find(".delete-button").click();
                                  }
                              });
                          } else if (iframesLocators.length > videoLocators.length) {
                              videoLocators = iframesLocators;
                          }
                          data.fields = {'video_locators': videoLocators};
                        }
                    if (metadataEditor) {
                        data.metadata = _.extend(data.metadata || {}, this.getChangedMetadata());
                    }
                // ... else log an error
                } else {
                    console.error('Cannot save xblock as it has no save method');
                }
                return data;
            },

            /**
             * Returns the metadata that has changed in the editor. This is a combination of the metadata
             * modified in the "Settings" editor, as well as any custom metadata provided by the component.
             */
            getChangedMetadata: function() {
                var metadataEditor = this.getMetadataEditor();
                return _.extend(metadataEditor.getModifiedMetadataValues(), this.getCustomMetadata());
            },

            /**
             * Returns custom metadata defined by a particular xmodule that aren't part of the metadata editor.
             * In particular, this is used for LaTeX high level source.
             */
            getCustomMetadata: function() {
                // Walk through the set of elements which have the 'data-metadata_name' attribute and
                // build up an object to pass back to the server on the subsequent POST.
                // Note that these values will always be sent back on POST, even if they did not actually change.
                var metadata, metadataNameElements, i, element, metadataName;
                metadata = {};
                metadataNameElements = this.$('[data-metadata-name]');
                for (i = 0; i < metadataNameElements.length; i++) {
                    element = metadataNameElements[i];
                    metadataName = $(element).data('metadata-name');
                    metadata[metadataName] = element.value;
                }
                return metadata;
            },

            getMode: function() {
                return this.mode;
            },

            selectMode: function(mode) {
                var showEditor = mode === 'editor',
                    dataEditor = this.getDataEditor(),
                    metadataEditor = this.getMetadataEditor();
                if (dataEditor) {
                    this.setEditorActivation(dataEditor, showEditor);
                }
                if (metadataEditor) {
                    this.setEditorActivation(metadataEditor.$el, !showEditor);
                }
                this.mode = mode;
            },

            setEditorActivation: function(editor, isActive) {
                editor.removeClass('is-active').removeClass('is-inactive');
                editor.addClass(isActive ? 'is-active' : 'is-inactive');
            }
        });

        return XBlockEditorView;
    }); // end define();
