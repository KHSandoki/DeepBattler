using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;

namespace DeepBattlerPlugin
{
    // On-screen Standard coach overlay (bottom-left). Polls agent_output.txt --
    // the file the Python claude_caller writes its analysis to -- every 0.5s and
    // shows the latest text. The Standard plugin shows it during a constructed
    // match and hides it otherwise. Built in code (no XAML) like DebugStateWindow.
    public class CoachWindow : Window
    {
        private readonly TextBlock _text;
        private readonly TextBlock _status;
        private readonly string _outputFile;
        private readonly DispatcherTimer _timer;
        private bool _allowClose;
        private string _last = "";

        public CoachWindow(string outputFile)
        {
            _outputFile = outputFile;

            Title = "DeepBattler 教練";
            Width = 470;
            Height = 340;
            Topmost = true;
            ShowInTaskbar = false;
            ResizeMode = ResizeMode.CanResizeWithGrip;
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = 20;
            Top = Math.Max(0, SystemParameters.PrimaryScreenHeight - Height - 80);
            Background = new SolidColorBrush(Color.FromArgb(238, 16, 22, 18));

            var root = new DockPanel { LastChildFill = true };

            var header = new TextBlock
            {
                Text = "  DeepBattler 教練  (可拖曳移動)",
                Foreground = Brushes.White,
                Background = new SolidColorBrush(Color.FromArgb(255, 34, 62, 42)),
                FontFamily = new FontFamily("Microsoft JhengHei"),
                FontSize = 13,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(6, 4, 6, 4)
            };
            DockPanel.SetDock(header, Dock.Top);
            root.Children.Add(header);

            _status = new TextBlock
            {
                Foreground = Brushes.Gray,
                FontFamily = new FontFamily("Consolas"),
                FontSize = 11,
                Padding = new Thickness(8, 2, 8, 2)
            };
            DockPanel.SetDock(_status, Dock.Bottom);
            root.Children.Add(_status);

            _text = new TextBlock
            {
                Foreground = Brushes.White,
                FontFamily = new FontFamily("Microsoft JhengHei"),
                FontSize = 14,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(8)
            };
            root.Children.Add(new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Content = _text
            });

            Content = root;

            MouseLeftButtonDown += (s, e) =>
            {
                try { if (e.ChangedButton == MouseButton.Left) DragMove(); }
                catch { }
            };

            _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(0.5) };
            _timer.Tick += (s, e) => Reload();
            _timer.Start();
            Reload();
        }

        private void Reload()
        {
            try
            {
                if (!File.Exists(_outputFile))
                {
                    _status.Text = "等待 Python 教練啟動… " + DateTime.Now.ToString("HH:mm:ss");
                    if (_text.Text.Length == 0)
                        _text.Text = "（還沒收到分析)\n請在新終端機執行:\npython claude_caller.py --mode standard";
                    return;
                }

                string content = null;
                for (int i = 0; i < 3; i++)
                {
                    try { content = File.ReadAllText(_outputFile); break; }
                    catch (IOException) { System.Threading.Thread.Sleep(60); }
                }
                if (content == null)
                    return;

                content = content.Trim();
                if (content == _last)
                    return;
                _last = content;
                _text.Text = content;
                _status.Text = "更新於 " + DateTime.Now.ToString("HH:mm:ss");
            }
            catch (Exception ex)
            {
                _status.Text = "讀取錯誤: " + ex.Message;
            }
        }

        // Show/hide from any thread (the plugin drives this by game mode).
        public void SetVisible(bool visible)
        {
            try
            {
                Dispatcher.BeginInvoke((Action)(() =>
                {
                    if (visible) { if (!IsVisible) Show(); }
                    else { if (IsVisible) Hide(); }
                }));
            }
            catch { }
        }

        public void ForceClose()
        {
            _allowClose = true;
            try { _timer?.Stop(); } catch { }
            try { Close(); } catch { }
        }

        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            if (!_allowClose)
            {
                e.Cancel = true;
                Hide();
            }
        }
    }
}
