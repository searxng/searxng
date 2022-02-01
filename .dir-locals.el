;;; .dir-locals.el
;;
;; Per-Directory Local Variables:
;;   https://www.gnu.org/software/emacs/manual/html_node/emacs/Directory-Variables.html
;;
;; .. hint::
;;
;;    If you get ``*** EPC Error ***`` (even after a jedi:install-server) in
;;    your emacs session, mostly you have jedi-mode enabled but the python
;;    enviroment is missed.  The python environment has to be next to the
;;    ``<repo>/.dir-locals.el`` in::
;;
;;       ./local/py3
;;
;; To setup such an environment, build target::
;;
;;     $ make pyenv.install
;;
;; Some buffer locals are referencing the project environment:
;;
;; - prj-root                                --> <repo>/
;; - nvm-dir                                 --> <repo>/.nvm
;; - python-environment-directory            --> <repo>/local
;; - python-environment-default-root-name    --> py3
;; - python-shell-virtualenv-root            --> <repo>/local/py3
;;       When this variable is set with the path of the virtualenv to use,
;;      `process-environment' and `exec-path' get proper values in order to run
;;      shells inside the specified virtualenv, example::
;;         (setq python-shell-virtualenv-root "/path/to/env/")
;; - python-shell-interpreter                --> <repo>/local/py3/bin/python
;;
;; Jedi, flycheck & other python stuff should use the 'python-shell-interpreter'
;; from the local py3 environment.
;;
;; For pyright support you need to install::
;;
;;    M-x package-install lsp-pyright
;;
;; Other useful jedi stuff you might add to your ~/.emacs::
;;
;;     (global-set-key [f6] 'flycheck-mode)
;;     (add-hook 'python-mode-hook 'my:python-mode-hook)
;;
;;     (defun my:python-mode-hook ()
;;       (add-to-list 'company-backends 'company-jedi)
;;       (require 'jedi-core)
;;       (jedi:setup)
;;       (define-key python-mode-map (kbd "C-c C-d") 'jedi:show-doc)
;;       (define-key python-mode-map (kbd "M-.")     'jedi:goto-definition)
;;       (define-key python-mode-map (kbd "M-,")     'jedi:goto-definition-pop-marker)
;;     )

((nil
  . ((fill-column . 80)
     (indent-tabs-mode . nil)
     (eval . (progn

               (add-to-list 'auto-mode-alist '("\\.html\\'" . jinja2-mode))

               ;; project root folder is where the `.dir-locals.el' is located
               (setq-local prj-root
                           (locate-dominating-file  default-directory ".dir-locals.el"))

               (setq-local python-environment-directory
                           (expand-file-name "./local" prj-root))

               ;; to get in use of NVM enviroment, install https://github.com/rejeep/nvm.el
               (setq-local nvm-dir (expand-file-name "./.nvm" prj-root))

               ;; use 'py3' enviroment as default
               (setq-local python-environment-default-root-name
                           "py3")

               (setq-local python-shell-virtualenv-root
                           (expand-file-name
                            python-environment-default-root-name python-environment-directory))

               (setq-local python-shell-interpreter
                           (expand-file-name
                            "bin/python" python-shell-virtualenv-root))))))
 (makefile-gmake-mode
  . ((indent-tabs-mode . t)))

 (yaml-mode
  . ((eval . (progn

               ;; flycheck should use the local py3 environment
               (setq-local flycheck-yaml-yamllint-executable
                           (expand-file-name "bin/yamllint" python-shell-virtualenv-root))

               (setq-local flycheck-yamllintrc
                           (expand-file-name  ".yamllint.yml" prj-root))

               (flycheck-checker . yaml-yamllint)))))

 (json-mode
  . ((eval . (progn
               (setq-local js-indent-level 4)
               (flycheck-checker . json-python-json)))))

 (js-mode
  . ((eval . (progn
               ;; use nodejs from the (local) NVM environment (see nvm-dir)
               (nvm-use-for-buffer)
               (setq-local js-indent-level 2)
               ;; flycheck should use the eslint checker from developer tools
               (setq-local flycheck-javascript-eslint-executable
                           (expand-file-name "node_modules/.bin/eslint" prj-root))

               (flycheck-mode)
               ))))

 (python-mode
  . ((eval . (progn
               ;; use nodejs from the (local) NVM environment (see nvm-dir)
               (nvm-use-for-buffer)
               (if (featurep 'lsp-pyright)
                   (lsp))
               (setq-local python-environment-virtualenv
                           (list (expand-file-name "bin/virtualenv" python-shell-virtualenv-root)
                                 ;;"--system-site-packages"
                                 "--quiet"))

               (setq-local pylint-command
                           (expand-file-name "bin/pylint" python-shell-virtualenv-root))

               ;; pylint will find the '.pylintrc' file next to the CWD
               ;;   https://pylint.readthedocs.io/en/latest/user_guide/run.html#command-line-options
               (setq-local flycheck-pylintrc
                           ".pylintrc")

               ;; flycheck & other python stuff should use the local py3 environment
               (setq-local flycheck-python-pylint-executable
                           python-shell-interpreter)

               ;; use 'M-x jedi:show-setup-info' and 'M-x epc:controller' to inspect jedi server
               ;; https://tkf.github.io/emacs-jedi/latest/#jedi:environment-root -- You
               ;; can specify a full path instead of a name (relative path). In that case,
               ;; python-environment-directory is ignored and Python virtual environment
               ;; is created at the specified path.
               (setq-local jedi:environment-root
                           python-shell-virtualenv-root)

               ;; https://tkf.github.io/emacs-jedi/latest/#jedi:server-command
               (setq-local jedi:server-command
                           (list python-shell-interpreter
                                 jedi:server-script))

               ;; jedi:environment-virtualenv --> see above 'python-environment-virtualenv'
               ;; is set buffer local!  No need to setup jedi:environment-virtualenv:
               ;;
               ;;    Virtualenv command to use.  A list of string.  If it is nil,
               ;;    python-environment-virtualenv is used instead.  You must set non-nil
               ;;    value to jedi:environment-root in order to make this setting work.
               ;;
               ;;    https://tkf.github.io/emacs-jedi/latest/#jedi:environment-virtualenv
               ;;
               ;; (setq-local jedi:environment-virtualenv
               ;;             (list (expand-file-name "bin/virtualenv" python-shell-virtualenv-root)
               ;;                   "--python"
               ;;                   "/usr/bin/python3.4"
               ;;                   ))
               ))))
 )
