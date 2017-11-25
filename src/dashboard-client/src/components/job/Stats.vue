<template>
    <div id="chart-cpu-mem" class="chart"></div>
</template>

<script>
import tauCharts from 'taucharts'
import 'taucharts/build/development/plugins/tauCharts.legend'
import 'taucharts/build/development/plugins/tauCharts.tooltip'

export default {
    name: 'Stats',
    props: ['job'],
    created () {
        this.job.loadStats()
    },
    mounted () {
        let draw = () => {
            if (!this.job.stats.length) {
                return
            }

            const config = {
                plugins: [
                    tauCharts.api.plugins.get('legend')(),
                    tauCharts.api.plugins.get('tooltip')(
                        {
                            fields: ['mem', 'cpu', 'date'],
                            formatters: {
                                mem: {
                                    label: 'Memory',
                                    format: (x) => {
                                        return (x + ' MiB')
                                    }
                                },
                                cpu: {
                                    label: 'CPU',
                                    format: (x) => {
                                        return (x + ' %')
                                    }
                                },
                                date: {
                                    label: 'Time',
                                    format: (x) => {
                                        return (x + ' s')
                                    }
                                }
                            }
                        })
                ],

                settings: {
                    fitModel: 'none'
                },

                sources: {
                    '?': {
                        dims: {},
                        data: []
                    },

                    '$': {
                        dims: {
                            x: { type: 'category', scale: 'ordinal' },
                            y: { type: 'category' }
                        },
                        data: [
                            { x: 1, y: 1 }
                        ]
                    },

                    '/': {
                        dims: {
                            date: { type: 'measure' },
                            cpu: { type: 'measure' },
                            mem: { type: 'measure' }
                        },
                        data: this.job.stats
                    }
                },

                scales: {

                    'xScale': { type: 'ordinal', source: '$', dim: 'x' },
                    'yScale': { type: 'ordinal', source: '$', dim: 'y' },

                    'x_date': { type: 'linear', source: '/', dim: 'date', autoScale: true, dimType: 'measure' },
                    'y_cpu': { type: 'linear', source: '/', dim: 'cpu', autoScale: true, dimType: 'measure' },
                    'y_mem': { type: 'linear', source: '/', dim: 'mem', autoScale: true, dimType: 'measure' },
                    'color_undefined': { type: 'color', source: '/', brewer: ['#f8ac59'] },
                    'color_undefined2': { type: 'color', source: '/', brewer: ['#23c6c8'] },
                    'size_undefined': { type: 'size', source: '/', min: 2, max: 10, mid: 5 },

                    'text:default': { type: 'value', source: '?' },
                    'split:default': { type: 'value', source: '?' }
                },

                unit: {
                    type: 'COORDS.RECT',
                    x: 'xScale',
                    y: 'yScale',
                    expression: {
                        source: '$',
                        inherit: false,
                        operator: false
                    },
                    guide: {
                        showGridLines: ''
                    },
                    frames: [
                        {
                            key: { x: 1, y: 1, i: 0 },
                            source: '$',
                            pipe: [],
                            units: [
                                {
                                    x: 'x_date',
                                    y: 'y_cpu',
                                    type: 'COORDS.RECT',
                                    expression: {
                                        inherit: false,
                                        operator: 'none',
                                        params: [],
                                        source: '/'
                                    },
                                    guide: {
                                        autoLayout: '',
                                        x: {
                                            autoScale: true,
                                            cssClass: 'x axis',
                                            hide: false,
                                            label: {
                                                cssClass: 'label',
                                                padding: 35,
                                                rotate: 0,
                                                size: 889.75,
                                                text: 'Time',
                                                textAnchor: 'middle'
                                            },
                                            padding: 20,
                                            rotate: 0,
                                            scaleOrient: 'bottom',
                                            textAnchor: 'middle'
                                        },
                                        y: {
                                            autoScale: true,
                                            cssClass: 'y axis',
                                            hide: false,
                                            label: {
                                                cssClass: 'label',
                                                padding: -40,
                                                rotate: -90,
                                                size: 431,
                                                text: 'CPU [%]',
                                                textAnchor: 'front'
                                            },
                                            padding: 20,
                                            rotate: 0,
                                            scaleOrient: 'right',
                                            textAnchor: 'front',
                                            tickFormat: 'x-num-auto'
                                        },
                                        padding: {
                                            b: 60,
                                            l: 100,
                                            r: 55,
                                            t: 10
                                        },
                                        showGridLines: 'xy'
                                    },

                                    units: [
                                        {
                                            size: 'size_undefined',
                                            type: 'ELEMENT.LINE',
                                            x: 'x_date',
                                            y: 'y_cpu',
                                            color: 'color_undefined',
                                            expression: {
                                                inherit: false,
                                                operator: 'none',
                                                params: [],
                                                source: '/'
                                            },
                                            guide: {
                                                anchors: false,
                                                cssClass: 'i-role-datum',
                                                showGridLines: 'xy',
                                                widthCssClass: '',
                                                color: {}
                                            }
                                        }
                                    ]
                                }
                            ]
                        }, {
                            key: { x: 1, y: 1, i: 1 },
                            source: '$',
                            pipe: [],
                            units: [
                                {
                                    x: 'x_date',
                                    y: 'y_mem',
                                    type: 'COORDS.RECT',
                                    expression: {
                                        inherit: false,
                                        operator: 'none',
                                        params: [],
                                        source: '/'
                                    },
                                    guide: {
                                        autoLayout: '',
                                        x: {
                                            autoScale: true,
                                            cssClass: 'x axis',
                                            hide: true,
                                            label: {
                                                cssClass: 'label',
                                                padding: 35,
                                                rotate: 0,
                                                size: 889.75,
                                                text: 'Time',
                                                textAnchor: 'middle'
                                            },
                                            padding: 20,
                                            rotate: 90,
                                            scaleOrient: 'bottom',
                                            textAnchor: 'middle'
                                        },
                                        y: {
                                            autoScale: true,
                                            cssClass: 'y axis',
                                            hide: false,
                                            label: {
                                                cssClass: 'label',
                                                padding: 40,
                                                rotate: -90,
                                                size: 431,
                                                text: 'Memory [MiB]',
                                                textAnchor: 'middle'
                                            },
                                            padding: 20,
                                            rotate: 0,
                                            scaleOrient: 'left',
                                            textAnchor: 'end',
                                            tickFormat: 'x-num-auto'
                                        },
                                        padding: {
                                            b: 60,
                                            l: 100,
                                            r: 55,
                                            t: 10
                                        },
                                        showGridLines: ''
                                    },

                                    units: [
                                        {
                                            size: 'size_undefined',
                                            type: 'ELEMENT.LINE',
                                            x: 'x_date',
                                            y: 'y_mem',
                                            color: 'color_undefined2',
                                            expression: {
                                                inherit: false,
                                                operator: 'none',
                                                params: [],
                                                source: '/'
                                            },
                                            guide: {
                                                anchors: false,
                                                cssClass: 'i-role-datum',
                                                showGridLines: 'xy',
                                                widthCssClass: '',
                                                color: {
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }

            const r = document.getElementById('chart-cpu-mem')

            if (!this.chart && r) {
                this.chart = new tauCharts.Plot(config)
                this.chart.renderTo('#chart-cpu-mem')
            }

            if (this.chart) {
                this.chart.refresh()
            }

            this.redraw = setTimeout(draw, 1000)
        }

        this.redraw = setTimeout(draw, 1000)
    },
    beforeDestroy () {
        clearTimeout(this.redraw)
    }

}
</script>

<style scoped>
.chart {
    width: 100%;
    height: 500px;
    margin: 0;
    padding: 0;
    float: left;
}
</style>
