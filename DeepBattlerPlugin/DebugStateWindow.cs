using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace DeepBattlerPlugin
{
    // Always-on debug window. Shows the raw game state DeepBattler sees, every
    // ~0.4s, whether or not a match is in progress. Built entirely in code (no
    // XAML) so it needs no extra build wiring. The Standard plugin owns it.
    public class DebugStateWindow : Window
    {
        private readonly TextBlock _text;
        private readonly TextBlock _status;

        public DebugStateWindow()
        {
            Title = "DeepBattler Debug";
            Width = 470;
            Height = 760;
            Topmost = true;            // float over Hearthstone (windowed / borderless)
            ShowInTaskbar = false;
            ResizeMode = ResizeMode.CanResizeWithGrip;
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = Math.Max(0, SystemParameters.PrimaryScreenWidth - Width - 20);
            Top = 20;
            Background = new SolidColorBrush(Color.FromArgb(235, 16, 18, 24));

            var root = new DockPanel { LastChildFill = true };

            var header = new TextBlock
            {
                Text = "  DeepBattler DEBUG  (drag to move • plugin button to hide)",
                Foreground = Brushes.White,
                Background = new SolidColorBrush(Color.FromArgb(255, 40, 44, 60)),
                FontFamily = new FontFamily("Segoe UI"),
                FontSize = 12,
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
                Foreground = Brushes.LightGreen,
                FontFamily = new FontFamily("Consolas"),
                FontSize = 12,
                TextWrapping = TextWrapping.NoWrap,
                Margin = new Thickness(8)
            };
            var scroller = new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                Content = _text
            };
            root.Children.Add(scroller);

            Content = root;

            MouseLeftButtonDown += (s, e) =>
            {
                try { if (e.ChangedButton == MouseButton.Left) DragMove(); }
                catch { /* DragMove throws if not left-button-down; ignore */ }
            };
        }

        // Safe to call from any thread.
        public void SetText(string body, string status)
        {
            try
            {
                Dispatcher.BeginInvoke((Action)(() =>
                {
                    _text.Text = body ?? "";
                    _status.Text = status ?? "";
                }));
            }
            catch { /* window may be closing */ }
        }

        private bool _allowClose;

        // The X button just hides the window so the plugin can re-show it;
        // ForceClose() lets the plugin really dispose it on unload.
        public void ForceClose()
        {
            _allowClose = true;
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
