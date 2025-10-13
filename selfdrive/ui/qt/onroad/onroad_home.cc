#include "selfdrive/ui/qt/onroad/onroad_home.h"

#include <QPainter>
#include <QStackedLayout>

#include "selfdrive/ui/qt/util.h"

OnroadWindow::OnroadWindow(QWidget *parent) : QWidget(parent) {
  QVBoxLayout *main_layout  = new QVBoxLayout(this);
  main_layout->setMargin(UI_BORDER_SIZE);
  QStackedLayout *stacked_layout = new QStackedLayout;
  stacked_layout->setStackingMode(QStackedLayout::StackAll);
  main_layout->addLayout(stacked_layout);

  nvg = new AnnotatedCameraWidget(VISION_STREAM_ROAD, this);

  QWidget * split_wrapper = new QWidget;
  split = new QHBoxLayout(split_wrapper);
  split->setContentsMargins(0, 0, 0, 0);
  split->setSpacing(0);
  split->addWidget(nvg);

  if (getenv("DUAL_CAMERA_VIEW")) {
    CameraWidget *arCam = new CameraWidget("camerad", VISION_STREAM_ROAD, this);
    split->insertWidget(0, arCam);
  }

  stacked_layout->addWidget(split_wrapper);

  alerts = new OnroadAlerts(this);
  alerts->setAttribute(Qt::WA_TransparentForMouseEvents, true);
  stacked_layout->addWidget(alerts);

  // setup stacking order
  alerts->raise();

  setAttribute(Qt::WA_OpaquePaintEvent);

  // We handle the connection of the signals on the derived class
#ifndef SUNNYPILOT
  QObject::connect(uiState(), &UIState::uiUpdate, this, &OnroadWindow::updateState);
  QObject::connect(uiState(), &UIState::offroadTransition, this, &OnroadWindow::offroadTransition);
#endif

  QPushButton *plusBtn = new QPushButton("+", this);
  QPushButton *minusBtn = new QPushButton("-", this);

  plusBtn->setGeometry(50, 300, 250, 250);  // top-left position, adjust as needed
  minusBtn->setGeometry(50, 550, 250, 250);

  plusBtn->setStyleSheet(
    "background-color: rgba(0,0,0,0);"  // fully transparent
    "border: none;"                     // remove border
    "font-size: 240px;"                 // large text
    "color: white;"                     // text color
  );

  minusBtn->setStyleSheet(
      "background-color: rgba(0,0,0,0);"
      "border: none;"
      "font-size: 280px;"
      "color: white;"
  );

  QObject::connect(plusBtn, &QPushButton::clicked, this, []() {
    Params().put("CruiseSpeedDelta", "1");
  });
  QObject::connect(minusBtn, &QPushButton::clicked, this, []() {
    Params().put("CruiseSpeedDelta", "-1");
  });
}

void OnroadWindow::updateState(const UIState &s) {
  if (!s.scene.started) {
    return;
  }

  alerts->updateState(s);
  nvg->updateState(s);

  QColor bgColor = bg_colors[s.status];
  if (bg != bgColor) {
    // repaint border
    bg = bgColor;
    update();
  }
}

void OnroadWindow::offroadTransition(bool offroad) {
  alerts->clear();
}

void OnroadWindow::paintEvent(QPaintEvent *event) {
  QPainter p(this);
  p.fillRect(rect(), QColor(bg.red(), bg.green(), bg.blue(), 255));
}
