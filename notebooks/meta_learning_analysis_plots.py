from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1.colorbar import colorbar
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib import path as mpath
from matplotlib import ticker
from matplotlib.transforms import Bbox
import numpy as np

from meta_learning_data_analysis import *


SAVE_PATH_PREFIX = 'meta_learning/figures'
DEFAULT_COLORMAP = 'tab10'
FIGURE_TEMPLATE = r'''\begin{{figure}}[!htb]
% \vspace{{-0.225in}}
\centering
\includegraphics[width=\linewidth]{{ch-results/figures/{save_path}}}
\caption{{ {{\bf FIGURE TITLE.}} FIGURE DESCRIPTION.}}
\label{{fig:results-{label_name}}}
% \vspace{{-0.2in}}
\end{{figure}}
'''
WRAPFIGURE_TEMPLATE = r'''\begin{{wrapfigure}}{{r}}{{0.5\linewidth}}
\vspace{{-.3in}}
\begin{{spacing}}{{1.0}}
\centering
\includegraphics[width=0.95\linewidth]{{ch-results/figures/{save_path}}}
\caption{{ {{\bf FIGURE TITLE.}} FIGURE DESCRIPTION.}}
\label{{fig:results-{label_name}}}
\end{{spacing}}
% \vspace{{-.25in}}
\end{{wrapfigure}}'''

def save(save_path, bbox_inches='tight'):
    if save_path is not None:
        save_path_no_ext = os.path.splitext(save_path)[0]
        print('Figure:\n')
        print(FIGURE_TEMPLATE.format(save_path=save_path, label_name=save_path_no_ext.replace('/', '-').replace('_', '-')))
        print('\n Wrapfigure:\n')
        print(WRAPFIGURE_TEMPLATE.format(save_path=save_path, label_name=save_path_no_ext.replace('/', '-').replace('_', '-')))
        print('')
        
        if not save_path.startswith(SAVE_PATH_PREFIX):
            save_path = os.path.join(SAVE_PATH_PREFIX, save_path)
        
        folder, filename = os.path.split(save_path)
        os.makedirs(folder, exist_ok=True)
        plt.savefig(save_path, bbox_inches=bbox_inches, facecolor=plt.gcf().get_facecolor(), edgecolor='none')


def full_extent(ax, pad=0.0):
    """Get the full extent of an axes, including axes labels, tick labels, and
    titles."""
    # For text objects, we need to draw the figure first, otherwise the extents
    # are undefined.
    ax.figure.canvas.draw()
    items = ax.get_xticklabels() + ax.get_yticklabels() 
#    items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
    items += [ax, ax.get_xaxis().get_label(), ax.get_yaxis().get_label()] # ax.title, 
    bbox = Bbox.union([item.get_window_extent() for item in items])

    return bbox.expanded(1.0 + pad, 1.0 + pad)
        

def raw_accuracies_plot(ax, results, colors, epochs_to_training_examples, 
                        log_x=False, shade_error=False, sem_n=1, ylim=None,
                        font_dict=None, x_label=None, y_label=None, y_label_right=False, 
                        title=None, hline_y=None, hline_style=None, title_font_dict=None, 
                        custom_x_ticks=None, text=None, text_x=None, text_y=None, 
                        num_tasks_to_plot=None, plot_consecutive=False):
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()
        
    num_colors = results.mean.shape[0]
    
    if num_tasks_to_plot is None:
        num_points = results.mean.shape[0]
    else:
        num_points = num_tasks_to_plot
    
    start_x_value = 0
    
    for row in range(num_points):
        max_x = np.argmax(np.isnan(results.mean[row, :]))
        x_values = np.arange(1, max_x + 1) * epochs_to_training_examples(row)
        
        if plot_consecutive and max_x > 0:
            x_values = x_values + start_x_value
            start_x_value = x_values[-1]
        
        y_means = results.mean[row, :max_x]
        
        ax.plot(x_values, y_means, color=colors(row / num_colors))
        
        if shade_error:
            if hasattr(sem_n, 'shape') and sem_n.shape == results.std.shape:
                n = sem_n[row, :max_x]
            else:
                n = sem_n
                
            y_stds = np.divide(results.std[row, :max_x], n ** 0.5)
            ax.fill_between(x_values, y_means - y_stds, y_means + y_stds,
                            color=colors(row / num_colors), alpha=0.25)        
            
    if hline_y is not None:
        hline = DEFAULT_COMPARISON_HLINE_STYLE.copy()
        
        if hline_style is not None:
            hline.update(hline_style)
        
        ax.axhline(hline_y, **hline)
        
    if ylim is not None:
        ax.set_ylim(ylim)

    if log_x:
        ax.set_xscale("log", nonposx='clip')

    if custom_x_ticks is not None:
        ax.set_xticks(custom_x_ticks)
        ax.set_xticklabels([f'{x // 1000}k' for x in custom_x_ticks])
        ax.xaxis.set_tick_params(rotation=45)
        ax.minorticks_off()
    
    # ax.set_xticks(np.arange(num_points) + 1)
    # ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    
    if x_label is None:
        x_label = f'{log_x and "Log(" or ""}Number of training trials{log_x and ")" or ""}'
    ax.set_xlabel(x_label, **font_dict)
        
    if y_label is None:
        y_label = f'{results.name}'
    ax.set_ylabel(y_label, **font_dict)
    
    if y_label_right:
        ax.yaxis.set_label_position("right")
    
    if title is None:
        title =  f'{results.name} vs. number of training trials'
    ax.set_title(title, **title_font_dict)
    
    if text is not None:
        if text_x is None:
            text_x = 512000
        if text_y is None:
            text_y = 0.75
            
        ax.text(text_x, text_y, text, font_dict, transform=ax.transAxes)

    
def both_raw_accuracy_plots(result_set, title, ylim=None, log_x=False, sem_n=1, dimension_index=COMBINED_INDEX,
                            shade_error=False, font_dict=None, hline_y=None, hline_style=None, 
                            num_tasks_to_plot=None, plot_consecutive=False,
                            first_task_title='First task accuracy by times trained',
                            new_task_title='New task accuracy by task order',
                            first_task_colormap=DEFAULT_COLORMAP, new_task_colormap=DEFAULT_COLORMAP, 
                            new_task_text=None, first_task_text=None, text_x=None, text_y=None, 
                            y_labels=('New task accuracy', 'First task accuracy'),
                            title_font_dict=None, add_colorbars=True, save_path=None, external_axes=None,
                            new_task_epochs_to_training_examples=None, first_task_epochs_to_training_examples=None):
    NROWS = 2
    NCOLS = 1
    COL_WIDTH = 6
    ROW_HEIGHT = 5 
    
    axes = []
    
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()
    
    if external_axes is None:
        figure = plt.figure(figsize=(NCOLS * COL_WIDTH, NROWS * ROW_HEIGHT))
        plt.subplots_adjust(top=0.9, hspace=0.4 + 0.1 * (len(new_task_title) > 0))
        
        figure.suptitle(title, fontsize=font_dict['fontsize'] * 1.5)
        
    if isinstance(first_task_colormap, str):
        first_task_colormap = plt.get_cmap(first_task_colormap)
        
    if isinstance(new_task_colormap, str):
        new_task_colormap = plt.get_cmap(new_task_colormap)
        
    if external_axes is not None:
        new_task_ax = external_axes[0]
    else:
        new_task_ax = plt.subplot(NROWS, NCOLS, 1) 
        axes.append(new_task_ax)
        
    results = result_set[dimension_index].new_task_accuracies
    title = new_task_title
    x_label = None
    y_label = y_labels[0]
    
    if new_task_epochs_to_training_examples is None:
        def new_task_epochs_to_training_examples(rep):
            return DATASET_CORESET_SIZE
    
    if new_task_ax is not None:
        raw_accuracies_plot(new_task_ax, results, new_task_colormap, new_task_epochs_to_training_examples, 
                            log_x=log_x, shade_error=shade_error, sem_n=result_set[dimension_index].accuracy_counts,
                            font_dict=font_dict, x_label=x_label, y_label=y_label, 
                            title=title, hline_y=hline_y, hline_style=hline_style, title_font_dict=title_font_dict,
                            custom_x_ticks=generate_custom_ticks(4000, 10, 2), text=new_task_text, 
                            text_x=text_x, text_y=text_y, num_tasks_to_plot=num_tasks_to_plot, plot_consecutive=plot_consecutive)
    
    if external_axes is not None:
        first_task_ax = external_axes[1]
    else:
        first_task_ax = plt.subplot(NROWS, NCOLS, 2)
        axes.append(first_task_ax)
        
    results = result_set[dimension_index].first_task_accuracies
    title = first_task_title
    x_label = None
    y_label = y_labels[1]
    
    if first_task_epochs_to_training_examples is None:
        def first_task_epochs_to_training_examples(row):
            return examples_per_epoch(1, row + 1)
        
    if first_task_ax is not None:
        raw_accuracies_plot(first_task_ax, results, first_task_colormap, first_task_epochs_to_training_examples, 
                            log_x=log_x, shade_error=shade_error, sem_n=result_set[dimension_index].accuracy_counts,
                            font_dict=font_dict, x_label=x_label, y_label=y_label,
                            title=title, hline_y=hline_y, hline_style=hline_style, title_font_dict=title_font_dict,
                            custom_x_ticks=generate_custom_ticks(), text=first_task_text, 
                            text_x=text_x, text_y=text_y, num_tasks_to_plot=num_tasks_to_plot, plot_consecutive=plot_consecutive)
        
    if add_colorbars:
        if first_task_ax is not None:
            add_colorbar_to_axes(first_task_ax, first_task_colormap, vmax=result_set[dimension_index].first_task_accuracies.mean.shape[0],
                                 y_label=NUM_TIMES_TRAINED_LABEL, y_label_font_dict=font_dict)
        if new_task_ax is not None:
            add_colorbar_to_axes(new_task_ax, new_task_colormap, vmax=result_set[dimension_index].first_task_accuracies.mean.shape[0],
                                 y_label=ORDINAL_POSITION_LABEL, y_label_font_dict=font_dict)

    if external_axes is None:
        if isinstance(save_path, list) or isinstance(save_path, tuple) and len(save_path) == len(axes):
            for ax, path in zip(axes, save_path):
                # extent = full_extent(ax).transformed(figure.dpi_scale_trans.inverted())
                extent = ax.get_tightbbox(figure.canvas.get_renderer()).transformed(figure.dpi_scale_trans.inverted())
                save(path, bbox_inches=extent)
        
        else:
            save(save_path)
            
        plt.show()

    
def generate_custom_ticks(scale=4000, max_power=8, min_power=0):
    return np.power(2, np.arange(min_power, max_power)) * scale
    

DEFAULT_LOG_SCALE_CUSTOM_TICKS = generate_custom_ticks()  # previously: (4500, 9000, 22500, 45000, 90000, 225000, 450000)


def fit_regression_line(x, y, log_x=False, log_y=False, index_increment=1):
    x = np.array(x)
    if log_x:
        x = np.log(x)
        
    y = np.array(y)
    if log_y:
        y = np.log(y)

    return np.polynomial.polynomial.polyfit(x, y, 1)


LINESTYLE_OPTIONS = ['--', ':']


def examples_by_times_trained_on(ax, results, colors, ylim=None, log_x=False, log_y=False, shade_error=False, sem_n=1,
                                 font_dict=None, x_label=None, y_label=None, y_label_right=False, 
                                 title=None, hline_y=None, hline_style=None, 
                                 y_custom_tick_labels=None, y_custom_tick_formatter=None,
                                 log_y_custom_ticks=DEFAULT_LOG_SCALE_CUSTOM_TICKS, title_font_dict=None,
                                 text=None, text_x=None, text_y=None, plot_regression=False, regression_legend=False,
                                 mark_lines=None, num_lines_to_mark=0, num_tasks_to_plot=None):
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()
        
    num_colors = results.mean.shape[0]
    
    if num_tasks_to_plot is None:
        num_points = results.mean.shape[0]
    else:
        num_points = num_tasks_to_plot
    
    # print(num_tasks_to_plot, num_points)
        
    nonzero_rows, nonzero_cols = np.nonzero(results.mean)
    means = [results.mean[r, c] for (r, c) in zip(nonzero_rows, nonzero_cols)]
    
    # ax.scatter(nonzero_rows + 1, means, 
    #                              color=[colors(x / num_points) for x 
    #                                     in abs(nonzero_cols - nonzero_rows)])
    
    reg_x_values = []
    reg_y_values = []
    
    for task in range(num_points):
        x_values = np.arange(1, num_colors - task + 1)
        reg_x_values.extend(x_values)
        y_means = np.diag(results.mean, task)
        reg_y_values.extend(y_means)
        
        linestyle = None
        if mark_lines == 'style' and task < num_lines_to_mark:
            linestyle = LINESTYLE_OPTIONS[task]
        
        # print(x_values)
        # print(y_means)
        
        ax.plot(x_values, y_means, marker='.', markersize=12, linestyle=linestyle, color=colors(task / num_colors))
        
        if shade_error:
            y_stds = np.diag(results.std, task) / (sem_n ** 0.5)
            ax.fill_between(x_values, y_means - y_stds, y_means + y_stds,
                            color=colors(task / num_colors), alpha=0.25)
            
    if hline_y is not None:
        if hline_style is None:
            hline_style = {}
        
        ax.axhline(hline_y, **hline_style)
        
    if plot_regression:
        (intercept, slope) = fit_regression_line(reg_x_values, reg_y_values, log_x=log_x)
        label = f'{log_y and "log(" or ""}y{log_y and ")" or ""} = {slope:.4} {log_x and "log(" or ""}x{log_x and ")" or ""} + {intercept:.4}'
        print(label)
        if plot_regression != 'print': 
            x_reg = np.arange(1, results.mean.shape[0] + 1)
            if log_x:
                y_reg = intercept + slope * np.log(x_reg)
            else:
                y_reg = intercept + slope * x_reg
            ax.plot(x_reg, y_reg, ls='--', label=label, lw=3, color='red')
        
        
    if ylim is not None:
        ax.set_ylim(ylim)

    if log_x:
        ax.set_xscale("log", nonposx='clip')
    
    ax.set_xticks(np.arange(num_points) + 1)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    
    if log_y:
        if log_y == 'simple':
            ax.set_yscale('log')
            ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.yaxis.set_minor_formatter(matplotlib.ticker.ScalarFormatter())
            
        else:
    #         ax.set_yscale("log", nonposy='clip')
            y_min, y_max = ax.get_ylim()
    #        y_min_pow_10 = np.ceil(y_min * np.log10(np.e))
    #        y_max_pow_10 = np.ceil(y_max * np.log10(np.e))

    #        y_powers_10 = np.arange(y_min_pow_10, y_max_pow_10)
    #        y_ticks = np.log(10) * y_powers_10
    #        y_tick_labels = [f'$10^{{ {int(y_tick)} }}$' for y_tick in y_powers_10]

            # Trying y-ticks at fixed intervals
            # real_y_min = np.exp(y_min)
            # real_y_max = np.exp(y_max)

            # scaled_y_min = np.ceil(real_y_min / log_y_tick_interval) * log_y_tick_interval
            # scaled_y_max = np.ceil(real_y_max / log_y_tick_interval) * log_y_tick_interval

            real_y_ticks = log_y_custom_ticks
            y_ticks = np.log(real_y_ticks)

            ax.set_yticks(y_ticks)
            ax.set_yticklabels([f'{y // 1000}k' for y in real_y_ticks])
    elif y_custom_tick_labels is not None:
        ax.set_yticklabels(y_custom_tick_labels)
        
    if y_custom_tick_formatter is not None:
        ax.yaxis.set_major_formatter(y_custom_tick_formatter)
        ax.yaxis.set_minor_formatter(y_custom_tick_formatter)
    
    if x_label is None:
        x_label = f'{log_x and "Log(" or ""}Number of times trained{log_x and ")" or ""}'
    ax.set_xlabel(x_label, **font_dict)
        
    if y_label is None:
        y_label = f'{results.name}'
    ax.set_ylabel(y_label, **font_dict)
    
    if y_label_right:
        ax.yaxis.set_label_position("right")
        
    if regression_legend:
        ax.legend(loc='best')
    
    if title is None:
        # title = f'{results.name} vs. number of tasks trained'
        title = 'Number of times trained on' 
        
    ax.set_title(title, **title_font_dict)
    
    if text is not None:
        if text_x is None:
            text_x = 0.1
        if text_y is None:
            text_y = 0.9
            
        ax.text(text_x, text_y, text, font_dict, transform=ax.transAxes)
    
    
def examples_by_num_tasks_trained(ax, results, colors, ylim=None, log_x=False, log_y=False, shade_error=False, sem_n=1,
                                  font_dict=None, x_label=None, y_label=None, y_label_right=False, 
                                  title=None, hline_y=None, hline_style=None, highlight_first_time=None, 
                                  y_custom_tick_labels=None, y_custom_tick_formatter=None,
                                  log_y_custom_ticks=DEFAULT_LOG_SCALE_CUSTOM_TICKS, 
                                  title_font_dict=None, text=None, text_x=None, text_y=None, 
                                  plot_regression=False, regression_legend=False, num_tasks_to_plot=None):
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()
        
    num_colors = results.mean.shape[0]
    
    if num_tasks_to_plot is None:
        num_points = results.mean.shape[0]
    else:
        num_points = num_tasks_to_plot
        
    nonzero_rows, nonzero_cols = np.nonzero(results.mean)
    means = [results.mean[r, c] for (r, c) in zip(nonzero_rows, nonzero_cols)]
    
    reg_x_values = []
    reg_y_values = []

    for task in range(num_points):
        x_values = np.arange(task + 1, num_colors + 1)
        reg_x_values.extend(x_values)
        y_means = results.mean[task, task:]
        reg_y_values.extend(y_means)
        
        y_stds = None
        if results.std is not None:
            y_stds = results.std[task, task:] / (sem_n ** 0.5)
        
        linestyle = '-'
        marker = '.'
        color = colors(task / num_colors)
        
        if task == 0 and highlight_first_time is not None:    
            if 'dash' in highlight_first_time:
                linestyle='--'
            
            if 'star' in highlight_first_time:
                marker='*'
            
            if 'color' in highlight_first_time:
                color = '#C0C0C0'
                
            if 'highlight' in highlight_first_time:
                if y_stds is None:
                    y_stds = 0.025
                    
                ax.plot(x_values, y_means - 3 * y_stds, linestyle=':', lw=2, color='red', alpha=1.0)
                ax.plot(x_values, y_means + 3 * y_stds, linestyle=':', lw=2, color='red', alpha=1.0)
            
        ax.plot(x_values, y_means, marker=marker, linestyle=linestyle, markersize=12, color=color)

        if shade_error:
            ax.fill_between(x_values, y_means - y_stds, y_means + y_stds,
                            color=color, alpha=0.25)
            
    if hline_y is not None:
        if hline_style is None:
            hline_style = {}
        
        ax.axhline(hline_y, **hline_style)
        
    if plot_regression:
        (intercept, slope) = fit_regression_line(reg_x_values, reg_y_values, log_x=log_x)
        label = f'{log_y and "log(" or ""}y{log_y and ")" or ""} = {slope:.3} {log_x and "log(" or ""}x{log_x and ")" or ""} + {intercept:.3}'
        print(label)
        if plot_regression != 'print': 
            x_reg = np.arange(1, results.mean.shape[0] + 1)
            if log_x:
                y_reg = intercept + slope * np.log(x_reg)
            else:
                y_reg = intercept + slope * x_reg
            ax.plot(x_reg, y_reg, ls='--', label=label, lw=3, color='red')
        
    
    if ylim is not None:
        ax.set_ylim(ylim)

    if log_x:
        ax.set_xscale("log", nonposx='clip')
    
    ax.set_xticks(np.arange(results.mean.shape[0]) + 1)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        
    if log_y:
        if log_y == 'simple':
            ax.set_yscale('log')
            ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.yaxis.set_minor_formatter(matplotlib.ticker.ScalarFormatter())

        else:
    #         ax.set_yscale("log", nonposy='clip')
            y_min, y_max = ax.get_ylim()
    #        y_min_pow_10 = np.ceil(y_min * np.log10(np.e))
    #        y_max_pow_10 = np.ceil(y_max * np.log10(np.e))

    #        y_powers_10 = np.arange(y_min_pow_10, y_max_pow_10)
    #        y_ticks = np.log(10) * y_powers_10
    #        y_tick_labels = [f'$10^{{ {int(y_tick)} }}$' for y_tick in y_powers_10]

            # Trying y-ticks at fixed intervals
            # real_y_min = np.exp(y_min)
            # real_y_max = np.exp(y_max)

            # scaled_y_min = np.ceil(real_y_min / log_y_tick_interval) * log_y_tick_interval
            # scaled_y_max = np.ceil(real_y_max / log_y_tick_interval) * log_y_tick_interval

            real_y_ticks = log_y_custom_ticks
            y_ticks = np.log(real_y_ticks)

            ax.set_yticks(y_ticks)
            ax.set_yticklabels([f'{y // 1000}k' for y in real_y_ticks])
            
    elif y_custom_tick_labels is not None:
        ax.set_yticklabels(y_custom_tick_labels)
        
    if y_custom_tick_formatter is not None:
        ax.yaxis.set_major_formatter(y_custom_tick_formatter)
        ax.yaxis.set_minor_formatter(y_custom_tick_formatter)
        
    if x_label is None:
        x_label = f'{log_x and "Log(" or ""}Episode number{log_x and ")" or ""}'    
    ax.set_xlabel(x_label, **font_dict)
        
    if y_label is None:
        y_label = f'{results.name}'
    ax.set_ylabel(y_label, **font_dict)
    
    if y_label_right:
        ax.yaxis.set_label_position("right")
    
    if regression_legend:
        ax.legend(loc='best')
    
    if title is None:
        title = f'Number of tasks trained on'
        
    ax.set_title(title, **title_font_dict)
    
    if text is not None:
        if text_x is None:
            text_x = 0.1
        if text_y is None:
            text_y = 0.9
        
        ax.text(text_x, text_y, text, font_dict, transform=ax.transAxes)

    
DEFAULT_Y_LABEL = 'Log(trials to criterion)'
ORDINAL_POSITION_LABEL = 'Task ordinal position'
NUM_TIMES_TRAINED_LABEL = 'Number of times trained'
SUBFIGURE_TEXT_POSITION = {
    8: [(0.10, 0.91), (0.10, 0.48),
        (0.305, 0.91), (0.305, 0.48),
        (0.51, 0.91), (0.51, 0.48),
        (0.715, 0.91), (0.715, 0.48)]
}
    

def plot_processed_results_all_dimensions(result_set, data_index, title, ylim=None, log_x=False, log_y=None,
                                          sem_n=1, shade_error=False, font_dict=None, plot_y_label=DEFAULT_Y_LABEL,
                                          times_trained_y_label=None, tasks_trained_y_label=None,
                                          times_trained_colormap=DEFAULT_COLORMAP, tasks_trained_colormap=DEFAULT_COLORMAP,
                                          log_y_custom_ticks=DEFAULT_LOG_SCALE_CUSTOM_TICKS, title_font_dict=None,
                                          dimension_names=CONDITION_ANALYSES_FIELDS, 
                                          dimension_indices=range(len(CONDITION_ANALYSES_FIELDS)),
                                          num_tasks_trained_highlight_first_time=None, 
                                          add_subfigure_texts=False, add_colorbars=True,
                                          save_path=None, external_axes=None, num_times_trained_title='',
                                          num_tasks_trained_title='', plot_regression=False, regression_legend=False,
                                          mark_lines=None, num_lines_to_mark=0, 
                                          num_tasks_to_plot_times_trained=None, num_tasks_to_plot_tasks_trained=None):
    NROWS = 2
    NCOLS = len(dimension_names)
    COL_WIDTH = 6.5
    ROW_HEIGHT = 5 
    WIDTH_SPACING = 1
    HEIGHT_SPACING = 0.75
    
    axes = []
    
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()
    
    if external_axes is None:
        figure = plt.figure(figsize=(NCOLS * COL_WIDTH + WIDTH_SPACING, NROWS * ROW_HEIGHT + HEIGHT_SPACING))
        plt.subplots_adjust(top=0.9 + 0.025 * (len(dimension_names) == 1), hspace=0.3, wspace=0.3)
        figure.suptitle(title, fontsize=font_dict['fontsize'] * 1.5)

    if log_y is None:
        log_y = 'log' in result_set[dimension_indices[0]][data_index].name
        
    if not hasattr(sem_n, '__len__'):
        sem_n = [sem_n] * len(CONDITION_ANALYSES_FIELDS)
        
    if isinstance(times_trained_colormap, str):
        times_trained_colormap = plt.get_cmap(times_trained_colormap)
        
    if isinstance(tasks_trained_colormap, str):
        tasks_trained_colormap = plt.get_cmap(tasks_trained_colormap)
        
    if times_trained_y_label is None:
        times_trained_y_label = plot_y_label
        
    if tasks_trained_y_label is None:
        tasks_trained_y_label = plot_y_label
        
    for ax_index, (dimension_index, dimension_name) in enumerate(zip(dimension_indices, dimension_names)):
        if external_axes is not None:
            num_times_trained_ax = external_axes[2 * ax_index]
        else:
            num_times_trained_ax = plt.subplot(NROWS, NCOLS, ax_index + 1)# NCOLS * dimension_index + 1)
            axes.append(num_times_trained_ax)
            
        results = result_set[dimension_index][data_index]
    
        title = num_times_trained_title
        if len(dimension_names) > 1:
            title = dimension_name.capitalize() # None  # sets the default title for this plot

        x_label = None
        y_label = ''
        if ax_index == 0:
            y_label = times_trained_y_label
        
        if num_times_trained_ax is not None:
            examples_by_times_trained_on(num_times_trained_ax, results, times_trained_colormap, ylim=ylim, 
                                         log_x=log_x, log_y=log_y, shade_error=shade_error, sem_n=sem_n[dimension_index],
                                         font_dict=font_dict, x_label=x_label, y_label=y_label, 
                                         title=title, log_y_custom_ticks=log_y_custom_ticks, title_font_dict=title_font_dict,
                                         plot_regression=plot_regression, regression_legend=regression_legend,
                                         mark_lines=mark_lines, num_lines_to_mark=num_lines_to_mark, 
                                         num_tasks_to_plot=num_tasks_to_plot_times_trained)

        if external_axes is not None:
            num_tasks_trained_ax = external_axes[2 * ax_index + 1]
        else:
            num_tasks_trained_ax = plt.subplot(NROWS, NCOLS, NCOLS + ax_index + 1) # NCOLS * dimension_index + 2)
            axes.append(num_tasks_trained_ax)
            
        # y_label = dimension_name.capitalize()
        title = num_tasks_trained_title
        
        if num_tasks_trained_ax is not None:
            examples_by_num_tasks_trained(num_tasks_trained_ax, results, tasks_trained_colormap, ylim=ylim, 
                                          log_x=log_x, log_y=log_y, shade_error=shade_error, sem_n=sem_n[dimension_index],
                                          font_dict=font_dict, x_label=x_label, y_label=tasks_trained_y_label,
                                          highlight_first_time=num_tasks_trained_highlight_first_time,
                                          title=title, log_y_custom_ticks=log_y_custom_ticks, title_font_dict=title_font_dict,
                                          plot_regression=plot_regression, regression_legend=regression_legend,
                                          num_tasks_to_plot=num_tasks_to_plot_tasks_trained)
        
        if (ax_index == len(dimension_names) - 1) and add_colorbars:
            if num_times_trained_ax is not None:
                add_colorbar_to_axes(num_times_trained_ax, times_trained_colormap, vmax=result_set[dimension_indices[-1]][data_index].mean.shape[0],
                                 y_label=ORDINAL_POSITION_LABEL, y_label_font_dict=font_dict)
            if num_tasks_trained_ax is not None:
                add_colorbar_to_axes(num_tasks_trained_ax, tasks_trained_colormap, vmax=result_set[dimension_indices[-1]][data_index].mean.shape[0],
                                 y_label=NUM_TIMES_TRAINED_LABEL, y_label_font_dict=font_dict)

    if add_subfigure_texts:
        subfigure_text_font_dict = font_dict.copy()
        subfigure_text_font_dict['fontsize'] += 4
        subfigure_text_font_dict['color'] = '#808080'
        subfigure_text_font_dict['weight'] = 'bold'
        
        num_subfigures = len(dimension_names) * 2
        for i in range(num_subfigures):
            pos = SUBFIGURE_TEXT_POSITION[num_subfigures][i]
            plt.text(pos[0], pos[1], f'({chr(97 + i)})', 
                     subfigure_text_font_dict, transform=figure.transFigure)

    if external_axes is None:
        if isinstance(save_path, list) or isinstance(save_path, tuple) and len(save_path) == len(axes):
            for ax, path in zip(axes, save_path):
                # extent = full_extent(ax).transformed(figure.dpi_scale_trans.inverted())
                extent = ax.get_tightbbox(figure.canvas.get_renderer()).transformed(figure.dpi_scale_trans.inverted())
                save(path, bbox_inches=extent)
        
        else:
            save(save_path)
            
        plt.show()

    
def add_colorbar_to_axes(ax, colors, vmin=1, vmax=10, y_label=None, y_label_font_dict=None, y_label_right=True):
    ax_divider = make_axes_locatable(ax)
    # add an axes to the right of the main axes.
    cax = ax_divider.append_axes("right", size="8%", pad="4%")
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cb = matplotlib.colorbar.ColorbarBase(cax, cmap=colors, norm=norm, ticks=np.arange(vmin, vmax + 1))
    
    # add an optional label
    if y_label is not None:
        if y_label_font_dict is None:
            y_label_font_dict = {}
        
        cax.set_ylabel(y_label, **y_label_font_dict)
        if y_label_right:
            cax.yaxis.set_label_position("right")
        
    
    
PER_MODEL_NROWS = 5
PER_MODEL_NCOLS = 4

PER_MODEL_COL_WIDTH = 5
PER_MODEL_ROW_HEIGHT = 6
    
    
def plot_per_model_per_dimension(baseline, per_query_replication, plot_func, super_title,
                                 font_dict=None, colormap=DEFAULT_COLORMAP, 
                                 ylim=None, log_x=True, log_y=True, shade_error=True, 
                                 sem_n=1, baseline_sem_n=1, data_index=None, plot_y_label=DEFAULT_Y_LABEL,
                                 title_font_dict=None, colorbar_y_label=None, save_path=None):
    
    fig, model_axes = plt.subplots(figsize=(PER_MODEL_NCOLS * (PER_MODEL_COL_WIDTH + 1), 
                                            PER_MODEL_NROWS * PER_MODEL_ROW_HEIGHT), 
                                   nrows=PER_MODEL_NROWS, ncols=1, sharey=True)
    
    for model_ax in model_axes:
        model_ax.tick_params(labelcolor=(1.,1.,1., 0.0), top=False, bottom=False, left=False, right=False)
        model_ax._frameon = False
    
    plt.subplots_adjust(top=0.94, hspace=0.35, wspace=0.2)
    
    if font_dict is None:
        font_dict = {}
        
    if title_font_dict is None:
        title_font_dict = font_dict.copy()

    if not hasattr(sem_n, '__len__'):
        sem_n = [sem_n] * len(CONDITION_ANALYSES_FIELDS)
        
    if not hasattr(baseline_sem_n, '__len__'):
        baseline_sem_n = [baseline_sem_n] * len(CONDITION_ANALYSES_FIELDS)
        
    if data_index is None:
        data_index = int(log_y)
        
    colors = plt.get_cmap(colormap)
    plt.suptitle(super_title, fontsize=font_dict['fontsize'] * 1.5)
    
    ax_title_font_dict = font_dict.copy()
    ax_title_font_dict['fontsize'] = ax_title_font_dict['fontsize'] + 4
    
    # plot the baseline
    model_axes[0].set_title(f'No query modulation', **ax_title_font_dict)
    
    for dimension_index, dimension_name in enumerate(CONDITION_ANALYSES_FIELDS):
        ax = fig.add_subplot(PER_MODEL_NROWS, PER_MODEL_NCOLS, dimension_index + 1)
            
        results = baseline[dimension_index][data_index]

        title = dimension_name.capitalize()

        x_label = None

        y_label = ''
        y_label_right = False
        if dimension_index == 0:
            y_label = plot_y_label
        # elif dimension_index == 3:
        #     y_label = f'No query\nmodulation'
        #     y_label_right = True

        plot_func(ax, results, colors, ylim=ylim, log_x=log_x, log_y=log_y, shade_error=shade_error, 
                  sem_n=baseline_sem_n[dimension_index], font_dict=font_dict, 
                  x_label=x_label, y_label=y_label, y_label_right=y_label_right, title=title,
                  title_font_dict=title_font_dict)
        
        if dimension_index == COMBINED_INDEX:
            add_colorbar_to_axes(ax, colors, vmax=baseline[0][data_index].mean.shape[0], y_label=colorbar_y_label, y_label_font_dict=font_dict)
    
    # plot per query
    for replication_level, replication_analyses in per_query_replication.items():
        model_axes[replication_level].set_title(f'Query modulation at conv-{replication_level}', **ax_title_font_dict)
        
        for dimension_index, dimension_name in enumerate(CONDITION_ANALYSES_FIELDS):
            ax = fig.add_subplot(PER_MODEL_NROWS, PER_MODEL_NCOLS, 
                             replication_level * PER_MODEL_NCOLS + dimension_index + 1)
            
            results = replication_analyses[dimension_index][data_index]

            title = ''
#             if replication_level == 1:
#                 title = dimension_name.capitalize()
                
            # x_label = ''
            # if replication_level + 1 == PER_MODEL_NROWS:
            x_label = None
                
            y_label = ''
            y_label_right = False
            if dimension_index == 0:
                y_label = plot_y_label
            # elif dimension_index == 3:
            #     y_label = f'Query modulation\nat conv-{replication_level}'
            #     y_label_right = True
    
            plot_func(ax, results, colors, ylim=ylim, log_x=log_x, log_y=log_y, shade_error=shade_error, 
                      sem_n=sem_n[dimension_index], font_dict=font_dict, 
                      x_label=x_label, y_label=y_label, y_label_right=y_label_right, title=title,
                      title_font_dict=title_font_dict)
        
            if dimension_index == COMBINED_INDEX:
                add_colorbar_to_axes(ax, colors, vmax=baseline[0][data_index].mean.shape[0], y_label=colorbar_y_label, y_label_font_dict=font_dict)
        
    save(save_path)
    plt.show()
    
    
def comparison_plot_per_model(baseline, per_query_replication, plot_func, super_title,
                              conditions=None, comparison_func=np.subtract,
                              font_dict=None, colormap=DEFAULT_COLORMAP, baseline_first=False,
                              ylim=None, data_index=None, log_x=True, log_y=True, shade_error=True, 
                              sem_n=1, baseline_sem_n=1, save_path=None):
    
    if conditions is None:
        conditions = list(range(len(CONDITION_ANALYSES_FIELDS)))
        
    if not hasattr(conditions, '__len__'):
        conditions = (conditions, )
        
    COMPARISON_NROWS = (PER_MODEL_NROWS - 1)
    COMPARISON_NCOLS = len(conditions)
    
    plt.figure(figsize=(COMPARISON_NCOLS * (PER_MODEL_COL_WIDTH + 5 - len(conditions)), 
                        COMPARISON_NROWS * PER_MODEL_ROW_HEIGHT))
    plt.subplots_adjust(top=0.925, hspace=0.25, wspace=0.15)
    
    if font_dict is None:
        font_dict = {}
        
    if data_index is None:
        data_index = int(log_y)

    if not hasattr(sem_n, '__len__'):
        sem_n = [sem_n] * len(CONDITION_ANALYSES_FIELDS)
        
    if not hasattr(baseline_sem_n, '__len__'):
        baseline_sem_n = [baseline_sem_n] * len(CONDITION_ANALYSES_FIELDS)
        
    colors = plt.get_cmap(colormap)
    plt.suptitle(super_title, fontsize=font_dict['fontsize'] * 1.5)
    
    # plot per query
    for replication_level, replication_analyses in per_query_replication.items():
        for index, (dimension_index, dimension_name) in enumerate([(c, CONDITION_ANALYSES_FIELDS[c]) for c in conditions]):
            replication_level_for_axes = replication_level - 1
            
            ax = plt.subplot(COMPARISON_NROWS, COMPARISON_NCOLS, 
                             replication_level_for_axes * COMPARISON_NCOLS + index + 1)


            if baseline_first:
                results_mean = comparison_func(baseline[dimension_index][data_index].mean,
                                               replication_analyses[dimension_index][data_index].mean,)
            else:
                results_mean = comparison_func(replication_analyses[dimension_index][data_index].mean,
                                               baseline[dimension_index][data_index].mean,
                                               )
            
            # TODO: fix the stddev computation
            results_std = baseline[dimension_index][data_index].std
            results = ResultSet(name='diff', mean=results_mean, std=results_std)
                
            title = ''
            if replication_level == 1:
                title = dimension_name.capitalize()
                
            x_label = ''
            if replication_level_for_axes + 1 == COMPARISON_NROWS:
                x_label = None
                
            y_label = ''
            if index == 0:
                y_label = f'Query modulation\nat conv-{replication_level}'
    
            plot_func(ax, results, colors, ylim=ylim, log_x=log_x, log_y=log_y, shade_error=shade_error, 
                      sem_n=sem_n[dimension_index], font_dict=font_dict, x_label=x_label, y_label=y_label, title=title)
        
    save(save_path)
    plt.show()
    
    
DEFAULT_COMPARISON_HLINE_STYLE = dict(linestyle='--', linewidth=4, color='black', alpha=0.25)

    
def combined_comparison_plots(baseline, per_query_replication, super_title,
                              dimension_index=COMBINED_INDEX, comparison_func=np.subtract,
                              font_dict=None, baseline_first=False, ylim=None, data_index=None, 
                              log_x=True, log_y=True, shade_error=True, sem_n=1, baseline_sem_n=1, 
                              title_font_dict=None, y_custom_tick_labels=None, y_custom_tick_formatter=None,
                              times_trained_colormap=DEFAULT_COLORMAP, tasks_trained_colormap=DEFAULT_COLORMAP,
                              null_hline_y=None, null_hline_style=None, plot_y_label='', add_colorbars=True,
                              save_path=None, external_axes=None, replication_levels=None, custom_titles=None):
        
    COMPARISON_NROWS = 2 #(PER_MODEL_NROWS - 1)
    COMPARISON_NCOLS = len(per_query_replication) #(PER_MODEL_NROWS - 1) # 2
    COL_WIDTH = 5
    ROW_HEIGHT = 5 
    WIDTH_SPACING = 1
    HEIGHT_SPACING = 0
    
    if font_dict is None:
        font_dict = {}
    
    if external_axes is None:
        figure = plt.figure(figsize=(COMPARISON_NCOLS * COL_WIDTH + WIDTH_SPACING, 
                                     COMPARISON_NROWS * ROW_HEIGHT + HEIGHT_SPACING))
        plt.subplots_adjust(top=0.9 - 0.035 * super_title.count('\n') + 0.02 * (len(per_query_replication) == 1), 
                            hspace=0.275, wspace=0.2)
        plt.suptitle(super_title, fontsize=font_dict['fontsize'] * 1.5)    
        
    if data_index is None:
        data_index = int(log_y)
        
    if null_hline_y is None:
        if comparison_func == np.subtract:
            null_hline_y = 0
        elif comparison_func == np.divide:
            null_hline_y = 1
        else:
            raise ValueError('If not using np.subract or np.divide, please provide null_hline_y value')
            
    hline_style = DEFAULT_COMPARISON_HLINE_STYLE.copy()
    if null_hline_style is not None:
        hline_style.update(null_hline_style)
    
    null_hline_style = hline_style
        
    times_trained_colors = plt.get_cmap(times_trained_colormap)
    tasks_trained_colors = plt.get_cmap(tasks_trained_colormap)
    
    # plot per query
    if replication_levels == None:
        replication_levels = sorted(per_query_replication.keys())
    
    for replication_level in replication_levels:
        replication_analyses = per_query_replication[replication_level]

        replication_level_for_axes = replication_level - 1
        
        if external_axes is not None:
            num_times_trained_ax = external_axes[0]
        else:
            num_times_trained_ax = plt.subplot(COMPARISON_NROWS, COMPARISON_NCOLS, replication_level_for_axes + 1)

        if baseline_first:
            results_mean = comparison_func(baseline[dimension_index][data_index].mean,
                                           replication_analyses[dimension_index][data_index].mean)
        else:
            results_mean = comparison_func(replication_analyses[dimension_index][data_index].mean,
                                           baseline[dimension_index][data_index].mean)

        if comparison_func == np.subtract:
            results_std = np.sqrt(np.power(replication_analyses[dimension_index][data_index].std, 2) + np.power(baseline[dimension_index][data_index].std, 2))
        else:
            # TODO: fix the stddev computation if we ever decide to use it here
            results_std = baseline[dimension_index][data_index].std
            
        results = ResultSet(name='diff', mean=results_mean, std=results_std)
    
        title = ''
        if custom_titles is not None:
            title = custom_titles[0]
            custom_titles = custom_titles[1:]
            
        else:
            title = f'Conv-{replication_level} modulation'
            

        x_label = None
        # if replication_level_for_axes + 1 == COMPARISON_NROWS:
        #     x_label = None  # use the default x-label

        y_label = '' 
        if replication_level_for_axes == 0:
            y_label = plot_y_label

        if num_times_trained_ax is not None:
            examples_by_times_trained_on(num_times_trained_ax, results, times_trained_colors, ylim=ylim, 
                                         log_x=log_x, log_y=log_y, shade_error=shade_error, sem_n=sem_n,
                                         font_dict=font_dict, x_label=x_label, y_label=y_label, 
                                         y_custom_tick_labels=y_custom_tick_labels, y_custom_tick_formatter=y_custom_tick_formatter,
                                         title=title, hline_y=null_hline_y, hline_style=null_hline_style,
                                         title_font_dict=title_font_dict)

        if external_axes is not None:
            num_tasks_trained_ax = external_axes[1]
        else:
            num_tasks_trained_ax = plt.subplot(COMPARISON_NROWS, COMPARISON_NCOLS, COMPARISON_NCOLS + replication_level_for_axes + 1)

        title = ''
        # y_label = f'Query modulation\nat conv-{replication_level}'

        if num_tasks_trained_ax is not None:
            examples_by_num_tasks_trained(num_tasks_trained_ax, results, tasks_trained_colors, ylim=ylim, 
                                          log_x=log_x, log_y=log_y, shade_error=shade_error, sem_n=sem_n,
                                          font_dict=font_dict, x_label=x_label, y_label=y_label,
                                          y_custom_tick_labels=y_custom_tick_labels, y_custom_tick_formatter=y_custom_tick_formatter,
                                          title=title, hline_y=null_hline_y, hline_style=null_hline_style,
                                          title_font_dict=title_font_dict)
        
        if (replication_level_for_axes == len(replication_levels) - 1) and add_colorbars:
            if num_times_trained_ax is not None:
                add_colorbar_to_axes(num_times_trained_ax, times_trained_colormap, vmax=baseline[3][data_index].mean.shape[0],
                                     y_label=ORDINAL_POSITION_LABEL, y_label_font_dict=font_dict)
            if num_tasks_trained_ax is not None:
                add_colorbar_to_axes(num_tasks_trained_ax, tasks_trained_colormap, vmax=baseline[3][data_index].mean.shape[0],
                                     y_label=NUM_TIMES_TRAINED_LABEL, y_label_font_dict=font_dict)
    
    if external_axes is None:
        save(save_path)
        plt.show()
    