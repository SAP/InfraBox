<template>
    <span>
            <span>
                <img :src="badgeUrl" height="20px" />
                <md-button class="md-icon-button" @click="openDialog(dialog_id)" style="padding-left:-16px; margin-left: -16px">
                    <i class="fa fa-fw fa-file-code-o" style="font-size: 19px; color: #757575"></i>
                </md-button>
            </span>
        <md-dialog md-open-from="#fab" md-close-to="#fab" :ref="dialog_id" width="100%">
            <md-dialog-title>Embed your badge</md-dialog-title>

            <md-dialog-content class="bg-white">
                <md-card class="main-card">
                    <div class="md-subtitle bg-light p-md">Markdown</div>
                    <div class="m-md">{{ markdown }}</div>
                </md-card>
                <md-card class="main-card">
                    <div class="md-subtitle bg-light p-md">HTML</div>
                    <div class="m-md">{{ html }}</div>
                </md-card>
                <md-card class="main-card">
                    <div class="md-subtitle bg-light p-md">RST</div>
                    <div class="m-md">{{ rst }}</div>
                </md-card>
                <md-card class="main-card">
                    <div class="md-subtitle bg-light p-md">Textile</div>
                    <div class="m-md">{{ textile }} </div>
                </md-card>
                <md-card class="main-card">
                    <div class="md-subtitle bg-light p-md">RDOC</div>
                    <div class="m-md">{{ rdoc }}</div>
                </md-card>
            </md-dialog-content>
            <md-dialog-actions>
                <md-button class="md-icon-button md-primary" @click="closeDialog(dialog_id)"><md-icon>close</md-icon></md-button>
            </md-dialog-actions>
        </md-dialog>
    </span>
</template>

<script>
import store from '../../store'

export default {
    props: ['job', 'subject', 'status', 'color'],
    created () {
        this.dialog_id = `${this.job.name}_${this.subject}_dialog`
        this.root_url = store.state.settings.INFRABOX_ROOT_URL
        this.statusEncoded = encodeURI(this.status)
        this.id = `badge-${this.subject}-${this.status}`
        this.id = this.id.replace(/\W+/g, '')
        this.url = `${this.root_url}/api/v1/projects/${this.job.project.id}/badge.svg?subject=${this.subject}&job_name=${this.job.name}`
        this.url = encodeURI(this.url)
        this.link = `${this.root_url}/dashboard/#/project/${this.job.project.name}`
        this.badgeUrl = `https://img.shields.io/badge/${this.subject}-${this.statusEncoded}-${this.color}.svg`
        this.markdown = `[![${this.subject}](${this.url})](${this.link})`
        this.html = `<a href="${this.link}"><img src="${this.url}" alt="${this.subject}"/></a>`
        this.rst = `.. image:: ${this.url} :target: ${this.link}`
        this.textile = `!${this.url}(${this.subject})!:${this.link}`
        this.rdoc = `{<img src="${this.url}" alt="${this.subject}"/>}[${this.link}]`
    },
    methods: {
        openDialog (ref) {
            this.$refs[ref].open()
        },
        closeDialog (ref) {
            this.$refs[ref].close()
        }
    }
}
</script>

<style scoped>
    .small-font{
        font-size: 13px;
    }
</style>
